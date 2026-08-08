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

    #{{register capability}}

    async def answer(self):
        try:
            transcript = await self.capability_worker.wait_for_complete_transcription()
            if not transcript or not transcript.strip():
                return

            # Deterministic route on the device. The transcript goes straight to the
            # engine; the LLM is never touched. `respond` returns a spoken answer or
            # nothing (nothing = not an exact-answer question).
            result = await self.capability_worker.send_devkit_capability_action(
                function_name="respond",
                args=[transcript],
                timeout=8,
            )
            spoken = self._spoken_response_from_result(result)

            if spoken:
                await self.capability_worker.speak(spoken)
            # else: no local answer -> stay quiet and let the agent handle the turn

        except Exception as error:
            self.worker.editor_logging_handler.error(f"Astral failed: {error}")
        finally:
            self.capability_worker.resume_normal_flow()

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
