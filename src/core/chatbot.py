"""
Translation chatbot for interactive editing
"""

from typing import Any, Dict

from .translation_engine import TranslationEngine


class TranslationChatbot:
    """Chatbot for interactive translation editing"""

    def __init__(self, translation_engine: TranslationEngine):
        self.translation_engine = translation_engine
        self.conversation_history = []
        self.current_translations = {}
        self.pending_changes = {}

    async def process_message(
        self, message: str, context: Dict[str, Any] = None
    ) -> str:
        """Process user message and return response"""

        self.conversation_history.append({"role": "user", "content": message})

        # Parse user intent
        intent = self._parse_intent(message)

        response = ""

        if intent == "change_translation":
            response = await self._handle_translation_change(message, context)
        elif intent == "query_translation":
            response = await self._handle_translation_query(message, context)
        elif intent == "batch_changes":
            response = await self._handle_batch_changes(message, context)
        elif intent == "apply_changes":
            response = await self._handle_apply_changes(context)
        else:
            response = await self._handle_general_chat(message, context)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _parse_intent(self, message: str) -> str:
        """Parse user intent from message"""

        message_lower = message.lower()

        if any(
            keyword in message_lower
            for keyword in ["thay đổi", "sửa", "change", "replace"]
        ):
            return "change_translation"
        elif any(
            keyword in message_lower
            for keyword in ["tìm", "tại sao", "why", "find", "search"]
        ):
            return "query_translation"
        elif any(
            keyword in message_lower
            for keyword in ["hàng loạt", "batch", "all", "tất cả"]
        ):
            return "batch_changes"
        elif any(
            keyword in message_lower for keyword in ["áp dụng", "apply", "save", "lưu"]
        ):
            return "apply_changes"
        else:
            return "general_chat"

    async def _handle_translation_change(
        self, message: str, context: Dict[str, Any]
    ) -> str:
        """Handle translation change requests"""

        # Extract source and target terms
        # This is simplified - in production you'd use more sophisticated NLP

        if "thay" in message.lower() and "thành" in message.lower():
            parts = message.split("thành")
            if len(parts) == 2:
                source_term = parts[0].replace("thay", "").strip().strip("\"'")
                target_term = parts[1].strip().strip("\"'")

                self.pending_changes[source_term] = target_term

                return f"Đã ghi nhận thay đổi: '{source_term}' -> '{target_term}'. Bạn có muốn áp dụng thay đổi này không?"

        return "Tôi không hiểu yêu cầu thay đổi của bạn. Vui lòng sử dụng format: 'Thay [từ cũ] thành [từ mới]'"

    async def _handle_translation_query(
        self, message: str, context: Dict[str, Any]
    ) -> str:
        """Handle translation queries"""

        # Search for terms in current translations
        search_results = []

        for source, target in self.current_translations.items():
            if any(
                term in source.lower() or term in target.lower()
                for term in message.lower().split()
            ):
                search_results.append(f"'{source}' -> '{target}'")

        if search_results:
            return f"Tìm thấy {len(search_results)} kết quả:\n" + "\n".join(
                search_results[:5]
            )
        else:
            return "Không tìm thấy kết quả phù hợp."

    async def _handle_batch_changes(self, message: str, context: Dict[str, Any]) -> str:
        """Handle batch changes"""

        # This would implement batch change functionality
        return "Chức năng thay đổi hàng loạt đang được phát triển."

    async def _handle_apply_changes(self, context: Dict[str, Any]) -> str:
        """Apply pending changes"""

        if not self.pending_changes:
            return "Không có thay đổi nào để áp dụng."

        # Apply changes to current translations
        for source, target in self.pending_changes.items():
            # Find and replace in current translations
            for key, value in self.current_translations.items():
                if source in key:
                    self.current_translations[key] = value.replace(source, target)
                elif source in value:
                    self.current_translations[key] = value.replace(source, target)

        count = len(self.pending_changes)
        self.pending_changes.clear()

        return f"Đã áp dụng {count} thay đổi thành công."

    async def _handle_general_chat(self, message: str, context: Dict[str, Any]) -> str:
        """Handle general chat"""

        return "Tôi có thể giúp bạn thay đổi các từ đã dịch. Hãy nói 'Thay [từ cũ] thành [từ mới]' để thay đổi bản dịch."
