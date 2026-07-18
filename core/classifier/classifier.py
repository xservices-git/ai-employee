"""Task classifier: phân loại input vào 1 trong 7 task types."""

from __future__ import annotations

import json
import re
from typing import Any

from core.common.config import get_settings
from core.common.errors import LLMError
from core.common.logging import get_logger
from core.common.types import AgentRole, A2AMessage, MessageType, TaskType

logger = get_logger(__name__)


CLASSIFIER_PROMPT = """Bạn là task classifier. Phân loại input user vào ĐÚNG 1 trong 7 loại sau:

1. data_processing - Xử lý/trích xuất/transform dữ liệu
   Ví dụ: "Tìm đơn hàng #123", "Cập nhật email khách A", "Import file CSV"

2. content_generation - Tạo nội dung văn bản
   Ví dụ: "Viết email xin lỗi", "Soạn hợp đồng", "Tạo báo cáo"

3. classification_routing - Phân loại/điều phối
   Ví dụ: "Phân loại 50 ticket support", "Điều phối khiếu nại"

4. monitoring_alerting - Giám sát/cảnh báo
   Ví dụ: "Kiểm tra tồn kho", "Cảnh báo khi đơn > 24h"

5. research_summarization - Nghiên cứu/tóm tắt
   Ví dụ: "Tóm tắt tài liệu", "Tìm hiểu thị trường Việt Nam"

6. scheduling_coordination - Lập lịch/điều phối
   Ví dụ: "Đặt lịch họp", "Nhắc việc", "Tìm slot trống"

7. decision_support - Hỗ trợ ra quyết định
   Ví dụ: "Phân tích rủi ro deal X", "Đề xuất phương án"

Trả lời CHỈ bằng JSON (không giải thích thêm):
{{
  "task_type": "<một trong 7 loại trên>",
  "domain": "<sales|customer_support|hr|admin|unknown>",
  "confidence": <0.0-1.0>,
  "reasoning": "<1 câu ngắn>"
}}

Input: {input}
"""


class Classifier:
    """LLM-based task classifier.

    Uses a small model (4B) for fast inference.
    Falls back to heuristic if LLM unavailable.
    """

    def __init__(self, ollama_client: Any | None = None):
        self.settings = get_settings()
        self._ollama = ollama_client
        self._model = self.settings.ollama_model_classifier

    async def classify(
        self,
        input_text: str,
        user_id: str,
        domain_hint: str | None = None,
    ) -> dict[str, Any]:
        """Classify input into task type.

        Returns: {task_type, domain, confidence, reasoning}
        """
        try:
            return await self._classify_llm(input_text, domain_hint)
        except LLMError as e:
            logger.warning("classifier.llm_failed_fallback_heuristic", error=str(e))
            return self._classify_heuristic(input_text)

    async def _classify_llm(
        self,
        input_text: str,
        domain_hint: str | None,
    ) -> dict[str, Any]:
        """Use Ollama LLM for classification."""
        if self._ollama is None:
            import ollama

            self._ollama = ollama.AsyncClient(host=self.settings.ollama_url)

        prompt = CLASSIFIER_PROMPT.format(input=input_text)

        try:
            response = await self._ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": 200},
            )
            text = response["message"]["content"]
            return self._parse_json_response(text, domain_hint)
        except Exception as e:
            raise LLMError(f"Ollama call failed: {e}") from e

    def _parse_json_response(
        self,
        text: str,
        domain_hint: str | None,
    ) -> dict[str, Any]:
        """Parse JSON from LLM response (handle markdown code blocks)."""
        # Try to extract JSON from code block
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise LLMError(f"No JSON in response: {text[:200]}")

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON: {e}") from e

        # Validate task_type
        task_type = data.get("task_type", "").strip()
        if task_type not in [t.value for t in TaskType]:
            # Try fuzzy match
            task_type = self._fuzzy_match_type(task_type)

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return {
            "task_type": task_type,
            "domain": data.get("domain", domain_hint or "unknown"),
            "confidence": confidence,
            "reasoning": data.get("reasoning", ""),
        }

    def _fuzzy_match_type(self, raw: str) -> str:
        """Fuzzy match to known task types."""
        raw_lower = raw.lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "data": TaskType.DATA_PROCESSING.value,
            "process": TaskType.DATA_PROCESSING.value,
            "content": TaskType.CONTENT_GENERATION.value,
            "write": TaskType.CONTENT_GENERATION.value,
            "generate": TaskType.CONTENT_GENERATION.value,
            "classify": TaskType.CLASSIFICATION_ROUTING.value,
            "route": TaskType.CLASSIFICATION_ROUTING.value,
            "monitor": TaskType.MONITORING_ALERTING.value,
            "alert": TaskType.MONITORING_ALERTING.value,
            "research": TaskType.RESEARCH_SUMMARIZATION.value,
            "summarize": TaskType.RESEARCH_SUMMARIZATION.value,
            "schedule": TaskType.SCHEDULING_COORDINATION.value,
            "coordinate": TaskType.SCHEDULING_COORDINATION.value,
            "decision": TaskType.DECISION_SUPPORT.value,
            "support": TaskType.DECISION_SUPPORT.value,
        }
        for key, value in mapping.items():
            if key in raw_lower:
                return value
        return TaskType.DATA_PROCESSING.value  # default

    def _classify_heuristic(self, input_text: str) -> dict[str, Any]:
        """Heuristic fallback when LLM unavailable."""
        text = input_text.lower()

        # Keyword-based heuristic
        rules = [
            (TaskType.DATA_PROCESSING, ["tìm", "cập nhật", "xóa", "import", "export", "query"]),
            (TaskType.CONTENT_GENERATION, ["viết", "soạn", "tạo nội dung", "draft", "compose"]),
            (TaskType.CLASSIFICATION_ROUTING, ["phân loại", "điều phối", "route", "classify"]),
            (TaskType.MONITORING_ALERTING, ["theo dõi", "cảnh báo", "monitor", "alert"]),
            (TaskType.RESEARCH_SUMMARIZATION, ["tóm tắt", "tìm hiểu", "research", "summarize"]),
            (TaskType.SCHEDULING_COORDINATION, ["lịch", "nhắc", "schedule", "reminder"]),
            (TaskType.DECISION_SUPPORT, ["phân tích", "đề xuất", "analyze", "recommend"]),
        ]

        scores: dict[TaskType, int] = {}
        for task_type, keywords in rules:
            scores[task_type] = sum(1 for kw in keywords if kw in text)

        best = max(scores.items(), key=lambda x: x[1])
        return {
            "task_type": best[0].value,
            "domain": "unknown",
            "confidence": 0.4 if best[1] > 0 else 0.2,
            "reasoning": f"heuristic match: {best[0].value} (score={best[1]})",
        }
