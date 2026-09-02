"""Astral background daemon — the local layer, without a trigger word.

WHAT THIS IS FOR

The Local Ability next door (main.py) only runs when OpenHome's cloud side matches a
trigger word: the platform hears the turn, decides it belongs to Astral, and hands the
transcript over. That is the well-documented path and it is the right default — when
Astral has nothing to say it says nothing and the agent takes the turn exactly as it
always did. Nothing here changes that.

What a trigger word cannot do is cover the turns nobody thought to register. "What is
twenty percent of twenty four thousand three hundred and fifty two" is arithmetic the
device answers exactly, in about a millisecond, offline — but only if something routed
it to the device first.

A background daemon is the one ability type that sees the session rather than a match:
it starts with the call, runs for the whole of it, survives sleep mode, and can read the
live transcript with get_full_message_history(). So it watches every turn, offers each
one to the device engine, and:

  • if the device has an exact answer, it interrupts and speaks that answer;
  • if the device has nothing — which is most turns — it does nothing at all, and
    OpenHome's normal routing handles the turn as usual.

That is the whole design. The local layer is a filter in front of the agent, not a
replacement for it, and the failure mode of the filter is silence.

  It also announces the local loop's timers. A timer set on this device has to be
  spoken by something that is still alive when it comes due; a foreground ability is a
  subprocess that has long since exited. This is the only thing here that speaks
  without being asked.

THE ONE RACE, STATED PLAINLY

The agent and this daemon see the same turn at the same time. The daemon has to be
first: it polls the transcript, asks the device, and calls send_interrupt_signal()
before it speaks — the documented primitive for exactly this, "stops current Personality
output, call before speak() from a daemon". A device answer costs a subprocess and a
table lookup; an LLM answer costs a round trip and speech synthesis. The daemon should
win comfortably. It is not guaranteed to: if the agent has already started talking the
interrupt cuts it mid-word and the user hears a stub before the real answer. The thing
that keeps that rare is that the device only ever answers what it can answer instantly —
respond() returns an empty string for everything else, and an empty string is never
worth interrupting for. This is the part that needs a room and a person to call proven;
see KNOWN-BUGS.md.

Files: background.py (this) is category=background_daemon. It shares devkit_functions.py
with the Local Ability, so there is one engine on the device, not two.
"""
import json
import time

try:                                            # the platform, on the device
    from src.agent.capability import MatchingCapability
    from src.main import AgentWorker
    from src.agent.capability_worker import CapabilityWorker
except ImportError:                             # off-device: the logic below is still testable
    MatchingCapability = object
    AgentWorker = object
    CapabilityWorker = None

# How often the transcript is read. This is a read of an in-process list, not a device
# call, so it is cheap; the number that matters is how long a turn can sit unnoticed
# while the agent is composing its own reply. A quarter of a second is comfortably
# inside the agent's own round trip. The docs' background-ability example sleeps 20
# seconds, which is right for an alert and useless for taking a turn.
POLL_SECONDS = 0.25
# Alerts are a device call, so they are checked far less often. Six seconds late on a
# ten-minute timer is not late.
ALERT_EVERY = 24                                # ticks, so ~6 s
DEVICE_TIMEOUT = 6                              # seconds for one respond() on the Pi


def last_user_turn(history):
    """The most recent thing the user said, as (index, text).

    get_full_message_history() returns the conversation as dicts. Nothing in the docs
    pins the key names, so this accepts the shapes that are actually used in the wild
    and returns nothing rather than guessing when it sees something else. Returning
    nothing means the daemon stays quiet, which is the safe direction.
    """
    if not history:
        return None, ""
    for i in range(len(history) - 1, -1, -1):
        turn = history[i]
        if not isinstance(turn, dict):
            continue
        role = (turn.get("role") or turn.get("speaker") or turn.get("sender") or "").lower()
        if role not in ("user", "human", "person"):
            continue
        text = turn.get("content") or turn.get("text") or turn.get("message") or ""
        if isinstance(text, list):              # some transports send content parts
            text = " ".join(str(p.get("text", p)) if isinstance(p, dict) else str(p) for p in text)
        text = str(text).strip()
        if text:
            return i, text
    return None, ""


def spoken_from(result):
    """The device's answer, or "" for 'not mine'. Anything unexpected is 'not mine'.

    An OFFER is also 'not mine'. When the device cannot answer here it can name the
    machines that could and ask which one — but that is a question, and a question needs
    somebody to take the reply. The foreground ability has run_io_loop for exactly that;
    a daemon has no turn of its own, and asking from here would leave the user answering
    into a conversation the agent is also in. So the daemon speaks answers and lets the
    offer go by, which means the agent handles that turn as it always would.
    """
    if not isinstance(result, dict) or not result.get("success"):
        return ""
    try:
        payload = json.loads((result.get("output") or "").strip() or "{}")
    except (ValueError, TypeError):
        return ""
    if not isinstance(payload, dict) or not payload.get("success"):
        return ""
    data = payload.get("data")
    if isinstance(data, dict) and data.get("offer"):
        return ""
    return str(payload.get("spoken_response") or "").strip()


class AstralDaemon(MatchingCapability):
    """Watches the session, answers what the device can answer, otherwise stays out."""

    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None
    background_daemon_mode: bool = True

    #{{register capability}}

    def call(self, worker: AgentWorker, background_daemon_mode: bool):
        # Order matters: CapabilityWorker reads both attributes in its constructor, so
        # they are set first. Getting this wrong is the documented way to build a daemon
        # that raises before it ever runs.
        self.worker = worker
        self.background_daemon_mode = background_daemon_mode
        self.capability_worker = CapabilityWorker(self)
        self.answered_turn = None
        self.last_text = ""
        self.worker.session_tasks.create(self.watch())

    async def watch(self):
        tick = 0
        while True:
            try:
                await self.take_turn_if_ours()
                if tick % ALERT_EVERY == 0:
                    await self.announce_due_alerts()
            except Exception as error:          # one bad turn must not end the session
                self._log(f"Astral daemon: {error}")
            tick += 1
            # session_tasks.sleep, never asyncio.sleep: the platform owns this loop's
            # lifetime and asyncio.sleep survives the session it belongs to.
            await self.worker.session_tasks.sleep(POLL_SECONDS)

    async def take_turn_if_ours(self):
        index, text = last_user_turn(self.capability_worker.get_full_message_history())
        if index is None or (index == self.answered_turn and text == self.last_text):
            return                              # nothing new since the last look
        self.answered_turn, self.last_text = index, text

        result = await self.capability_worker.send_devkit_capability_action(
            function_name="respond", args=[text], timeout=DEVICE_TIMEOUT)
        spoken = spoken_from(result)
        if not spoken:
            return                              # not ours: the agent's turn, untouched

        await self.capability_worker.send_interrupt_signal()
        await self.capability_worker.speak(spoken)

    async def announce_due_alerts(self):
        """Speak any timer or reminder that has come due on the device."""
        result = await self.capability_worker.send_devkit_capability_action(
            function_name="due_alerts", args=[], timeout=DEVICE_TIMEOUT)
        spoken = spoken_from(result)
        if not spoken:
            return
        await self.capability_worker.send_interrupt_signal()
        await self.capability_worker.speak(spoken)

    def _log(self, message):
        handler = getattr(self.worker, "editor_logging_handler", None)
        if handler is not None:
            handler.error(message)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
