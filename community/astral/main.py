import json
from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker


class AstralCapability(MatchingCapability):
    """Astral — a deterministic layer for the exact-answer class.

    On a trigger word the transcript goes straight to the device, which answers with
    plain pattern-and-table code (time, date, math, money, unit conversions, telemetry).
    No LLM routing on the cloud side, no model on the device side. If Astral has no
    answer, it speaks nothing and hands the turn back so the agent takes it.
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
            # engine; the LLM is never touched. `respond` returns a spoken answer, an
            # offer of somewhere else to send it, or nothing (nothing = not an
            # exact-answer question).
            result = await self.capability_worker.send_devkit_capability_action(
                function_name="respond",
                args=[transcript],
                timeout=8,
            )
            spoken = self._spoken_response_from_result(result)
            data = self._data_from_result(result)

            if spoken and data.get("offer"):
                await self._offer_a_route(transcript, spoken, data.get("routes") or [])
            elif spoken:
                await self.capability_worker.speak(spoken)
            # else: no local answer -> stay quiet and let the agent handle the turn

        except Exception as error:
            self.worker.editor_logging_handler.error(f"Astral failed: {error}")
        finally:
            self.capability_worker.resume_normal_flow()

    async def _offer_a_route(self, transcript, question, routes):
        """The device knows what was asked and cannot do it here. Ask where to send it.

        This is the ranking speaking: it only ever gets here for a question the device
        recognised and priced, never for chatter, so the question is not a shrug — it
        names the places that could actually answer. The reply decides:

          the cloud  -> say nothing, and the agent takes the turn, because on this path
                        the agent IS the cloud. Nothing is uploaded by this ability.
          a machine  -> the device asks it over the local network and speaks the answer.
          anything else, or no answer at all -> nothing is sent anywhere.
        """
        reply = await self.capability_worker.run_io_loop(question)
        chosen = self._route_named(reply or "", routes)
        if chosen is None or chosen == "cloud":
            return                              # the agent's turn, untouched
        result = await self.capability_worker.send_devkit_capability_action(
            function_name="route_answer", args=[chosen, transcript], timeout=30)
        spoken = self._spoken_response_from_result(result)
        if spoken:
            await self.capability_worker.speak(spoken)

    @staticmethod
    def _route_named(reply, routes):
        """Which offered route the answer picked, or None for no and for silence.

        A bare yes is only an answer when one place was offered. With two, a person
        answers with the name, and taking a plain "yes" as the first of them would be
        putting words in their mouth about where their words go.
        """
        said = " " + str(reply).lower().strip(" .!?") + " "
        words = {"mac": ("mac", "computer", "laptop", "desktop"),
                 "phone": ("phone", "mobile", "cell"),
                 "cloud": ("cloud", "internet", "online", "you")}
        for route in routes:
            if any(f" {w} " in said for w in words.get(route, (route,))):
                return route
        if len(routes) == 1 and any(f" {y} " in said for y in
                                    ("yes", "yeah", "yep", "sure", "ok", "okay", "please", "go ahead")):
            return routes[0]
        return None

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
        if not payload.get("success"):
            return ""
        return (payload.get("spoken_response") or "").strip()

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.answer())
