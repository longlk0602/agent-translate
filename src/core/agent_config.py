"""
Configuration for React Translation Agent
"""

import os
from typing import Dict, Any, Optional

DEFAULT_LLM_CONFIG = {
    "providers": {
        "openai": {
            "type": "openai",
            "api_key": None,  # Will be loaded from environment
            "model": "gpt-4.1-mini",
            "temperature": 0.3,
            "max_tokens": 2000
        },
        "azure_openai": {
            "type": "azure_openai", 
            "api_key": None,  # Will be loaded from environment
            "endpoint": None,  # Will be loaded from environment
            "model": "gpt-4.1-mini",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    },
    "default_provider": "openai"
}

SYSTEM_PROMPT = """Bạn là một trợ lý AI chuyên nghiệp giúp chỉnh sửa và cải thiện bản dịch tài liệu.

**Khả năng của bạn:**
- Tìm kiếm và phân tích nội dung trong tài liệu (PPTX, DOCX, Excel)
- Thay thế text trong tài liệu một cách chính xác
- Cung cấp phân tích chi tiết về nội dung và cấu trúc tài liệu
- Hỗ trợ nhiều định dạng: PowerPoint slides, Word documents, Excel spreadsheets

**Nguyên tắc làm việc:**
1. Luôn xác nhận với người dùng trước khi thực hiện thay đổi quan trọng
2. Cung cấp thông tin chi tiết về những gì bạn tìm thấy và sẽ thay đổi
3. Giải thích lý do cho các đề xuất chỉnh sửa
4. Hỗ trợ cả tiếng Việt và tiếng Anh
5. Ưu tiên độ chính xác và giữ nguyên định dạng của tài liệu

**Khi người dùng yêu cầu thay đổi:**
- Sử dụng search tool để tìm text cần thay đổi
- Xác nhận với người dùng về những gì tìm thấy
- Thực hiện replace chính xác
- Báo cáo kết quả chi tiết

**Khi người dùng muốn tìm hiểu tài liệu:**
- Sử dụng analyze tool để cung cấp thông tin tổng quan
- Sử dụng search tool để tìm nội dung cụ thể
- Cung cấp thông tin về cấu trúc và nội dung

Hãy luôn thân thiện, chuyên nghiệp và hỗ trợ tốt nhất có thể!"""

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration with environment variables"""
    
    config = DEFAULT_LLM_CONFIG.copy()
    
    # Load OpenAI config from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        config["providers"]["openai"]["api_key"] = openai_key
    
    # Load Azure OpenAI config from environment  
    azure_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    if azure_key and azure_endpoint:
        config["providers"]["azure_openai"]["api_key"] = azure_key
        config["providers"]["azure_openai"]["endpoint"] = azure_endpoint
    
    # Determine default provider based on available keys
    if azure_key and azure_endpoint:
        config["default_provider"] = "azure_openai"
    elif openai_key:
        config["default_provider"] = "openai"
    else:
        # Try OpenAI first if no keys found
        config["default_provider"] = "openai"
    
    return config

def get_agent_config(llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get complete agent configuration"""
    
    if llm_config is None:
        llm_config = get_llm_config()
    
    return {
        "llm_config": llm_config,
        "system_prompt": SYSTEM_PROMPT,
        "max_iterations": 10,
        "max_conversation_length": 50,
        "tools": {
            "pptx": ["search", "replace", "analyze", "slide_info"],
            "docx": ["search", "replace", "analyze"], 
            "excel": ["search", "replace", "analyze", "get_range"]
        }
    }
