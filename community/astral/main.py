import json
import re
from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

# ── route words: an exact copy of hub/route_words.py. The hub suite fails if they differ. ──
# Every offered route is picked by any of these, said as a complete selection.
WORDS = {
    "phone": ("phone", "iphone", "android", "mobile", "cell", "cell phone", "cellphone", "smartphone"),
    "mac": ("computer", "mac", "macbook", "imac", "laptop", "desktop", "pc", "windows pc", "linux box"),
    "local-model": ("here", "locally", "this device", "the model", "local model", "model on this device"),
    "cloud:openhome": ("openhome", "open home", "openhome agent", "open home agent", "agent"),
}
# A named cloud provider is picked by its own name.
PROVIDERS = {
    "anthropic": ("claude", "anthropic"), "openai": ("chatgpt", "chat gpt", "openai", "gpt"),
    "google": ("gemini", "google"), "xai": ("grok",), "groq": ("groq",),
    "mistral": ("mistral",), "deepseek": ("deepseek", "deep seek"), "openrouter": ("openrouter",),
    "together": ("together",), "openhome": ("openhome", "open home", "openhome agent", "open home agent", "agent"),
}
# "The cloud" picks a cloud route only when exactly one is offered.
CLOUD_WORDS = ("cloud", "internet", "online")
REFUSAL = re.compile(r"\b(?:no|nope|nah|not|never|neither|none|cancel|stop|don't|dont|do not|"
                     r"forget it|forget about it|leave it|skip it|without)\b")
_YES_WORD = r"(?:yes|yeah|yep|yup|sure|ok|okay|go ahead|do it|send it|go for it)"
YES = re.compile(rf"(?:please )?{_YES_WORD}(?: {_YES_WORD})*(?: please| thanks| thank you)?|please")
# A route's name can occur in a question, a hedge or a comparison ("what is the cloud",
# "maybe my computer", "mac or cloud"). Only a complete selection authorizes sending: an
# optional yes, an optional verb, an optional determiner, the name, an optional please.
PREFIX = (r"(?:please )?(?:(?:yes|yeah|yep|sure|ok|okay) )?"
          r"(?:(?:(?:can|could|would) you )?"
          r"(?:ask|use|try|go with|send (?:it|that|this) to|do it|run it|answer it|do it on|do that on) )?"
          r"(?:the |my |your |on |on the |on my )?")
SUFFIX = r"(?: please| thanks| thank you)?"
ORDINAL = re.compile(r"(?:the )?(first|1st|second|2nd|third|3rd|last)(?: one)?" + SUFFIX)
_ORDINAL_INDEX = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2, "last": -1}


def normalize(reply) -> str:
    """Lower case, curly apostrophes straightened, punctuation gone, spaces single."""
    text = str(reply or "").lower().replace("\u2019", "'")
    return " ".join(re.findall(r"[a-z0-9']+", text))


def words_for(route: str, offered) -> tuple:
    """The words that pick `route` out of this particular offer."""
    if route in WORDS:
        words = WORDS[route]
    elif route.startswith("cloud:"):
        provider = route.split(":", 1)[1]
        words = PROVIDERS.get(provider, (provider,))
    else:
        words = (route,)
    clouds = [r for r in offered if r == "cloud" or r.startswith("cloud:")]
    if (route == "cloud" or route.startswith("cloud:")) and len(clouds) == 1:
        words = tuple(words) + tuple(w for w in CLOUD_WORDS if w not in words)
    return tuple(words)


def _mentions(said: str, phrase: str) -> bool:
    return re.search(r"(?:^| )" + re.escape(phrase) + r"(?: |$)", said) is not None


def choose(reply, offered) -> tuple:
    """(route or None, how). See the module note for what each `how` means."""
    offered = list(offered or [])
    said = normalize(reply)
    if not said or not offered:
        return None, "unclear"
    if REFUSAL.search(said):
        return None, "refused"
    selected = [r for r in offered
                if any(re.fullmatch(PREFIX + re.escape(w) + SUFFIX, said) for w in words_for(r, offered))]
    if len(selected) == 1:
        return selected[0], "named"
    m = ORDINAL.fullmatch(said)
    if m:
        index = _ORDINAL_INDEX[m.group(1)]
        if -len(offered) <= index < len(offered):
            return offered[index], "ordinal"
    if YES.fullmatch(said):
        first = offered[0]
        if len(offered) == 1 or not (first == "cloud" or first.startswith("cloud:")):
            return first, "yes"                  # the nearest: the ranking names it first
        return None, "ambiguous"                 # only elsewheres offered: say which
    mentioned = [r for r in offered if any(_mentions(said, w) for w in words_for(r, offered))]
    if len(selected) > 1 or len(mentioned) > 1:
        return None, "ambiguous"                 # "your phone or the agent": ask which
    return None, "unclear"


def which_one(spoken_names) -> str:
    """The one follow-up question, when the answer did not pick between two or more."""
    names = list(spoken_names)
    if len(names) == 2:
        return f"Which one: {names[0]}, or {names[1]}?"
    return "Which one: " + ", ".join(names[:-1]) + f", or {names[-1]}?"
# ── end of the copy ──


# What each route is called out loud, for the one follow-up question when a reply did not
# pick between them. The device sends its own names with an offer; these are the fallback.
SPOKEN = {"phone": "your phone", "mac": "your computer", "local-model": "the model on the device",
          "cloud": "the cloud", "cloud:openhome": "the OpenHome agent"}


class AstralCapability(MatchingCapability):
    """Astral — a deterministic layer for the exact-answer class.

    On a trigger word the transcript goes straight to the device, which answers with
    plain pattern-and-table code (time, date, math, money, unit conversions, telemetry).
    This wrapper does not call a model. The local hub may use its configured local
    model for supported requests. OpenHome supplies the transcript and speech; if
    Astral has no answer, it hands the turn back to the configured platform agent.
    """

    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    #{{register capability}}  # noqa: E265 — the platform replaces this whole
    # line on upload and requires it verbatim, with no space after the hash

    async def answer(self):
        try:
            transcript = await self.capability_worker.wait_for_complete_transcription()
            if not transcript or not transcript.strip():
                return

            # Deterministic route on the device. The transcript goes straight to the
            # engine. `respond` returns a spoken answer, an
            # offer of somewhere else to send it, or nothing (nothing = not an
            # exact-answer question).
            result = await self.capability_worker.send_devkit_capability_action(
                function_name="respond",
                args=[transcript],
                timeout=25,
            )
            spoken = self._spoken_response_from_result(result)
            data = self._data_from_result(result)

            if spoken and data.get("offer"):
                await self._offer_a_route(transcript, spoken, data.get("routes") or [],
                                          data.get("names") or [])
            elif spoken:
                await self.capability_worker.speak(spoken)
            # else: no local answer -> stay quiet and let the agent handle the turn

        except Exception as error:
            self.worker.editor_logging_handler.error(f"Astral failed: {error}")
        finally:
            self.capability_worker.resume_normal_flow()

    async def _offer_a_route(self, transcript, question, routes, names=()):
        """The device knows what was asked and cannot do it here. Ask where to send it.

        This is the ranking speaking: it only ever gets here for a question the device
        recognised and priced, never for chatter, so the question is not a shrug. It names
        the places that could actually answer, and the reply is read by choose(), the same
        reading the house loop uses:

          a machine      -> the device asks it over the local network and speaks the answer
          the agent      -> say nothing: the agent takes the turn, as the platform intends
          not a choice   -> one more question ("Which one: your phone, or the OpenHome agent?")
          no, or unclear -> "Okay." and nothing is sent anywhere, the agent included
        """
        reply = await self.capability_worker.run_io_loop(question)
        chosen, how = choose(reply or "", routes)
        if how == "ambiguous":
            spoken = list(names) if len(names) == len(routes) else [SPOKEN.get(r, r) for r in routes]
            reply = await self.capability_worker.run_io_loop(which_one(spoken))
            chosen, how = choose(reply or "", routes)
        if chosen is None:
            await self.capability_worker.speak("Okay.")
            return
        if chosen == "cloud" or chosen == "cloud:openhome":
            return                              # the agent's turn, untouched
        result = await self.capability_worker.send_devkit_capability_action(
            function_name="route_answer", args=[chosen, transcript], timeout=30)
        spoken = self._spoken_response_from_result(result)
        if spoken:
            await self.capability_worker.speak(spoken)

    @staticmethod
    def _route_named(reply, routes):
        """Which offered route the answer picked, or None: choose() without the follow-up."""
        return choose(reply, routes)[0]

    def _data_from_result(self, result):
        """The structured half of the device's answer. Never raises; {} means nothing."""
        if not isinstance(result, dict) or not result.get("success"):
            return {}
        try:
            payload = json.loads((result.get("output") or "").strip() or "{}")
        except (ValueError, TypeError):
            return {}
        data = payload.get("data") if isinstance(payload, dict) else None
        return data if isinstance(data, dict) else {}

    def _spoken_response_from_result(self, result):
        if not isinstance(result, dict):
            return ""
        if not result.get("success"):
            self.worker.editor_logging_handler.error(
                f"Astral device call failed: {result.get('error')}"
            )
            return ""
        output = (result.get("output") or "").strip()
        if not output:
            return ""
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            self.worker.editor_logging_handler.error(f"Astral: invalid device output: {output}")
            return ""
        if not isinstance(payload, dict) or not payload.get("success"):
            return ""
        spoken = payload.get("spoken_response")
        return spoken.strip() if isinstance(spoken, str) else ""

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.answer())
