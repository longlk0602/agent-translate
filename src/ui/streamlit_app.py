"""
Streamlit interface for session-based translation workflow
"""

from pydoc import text
import streamlit as st
import requests
import json
import time
from pathlib import Path
import tempfile
import os

# Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_status():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        return True, response.json()
    except requests.exceptions.ConnectionError:
        return False, None

def upload_and_create_session(file, target_lang, source_lang, model_provider, model_name, temperature, context):
    """Upload file and create translation session"""
    try:
        # Prepare form data
        files = {'file': (file.name, file.getvalue(), file.type)}
        data = {
            'target_lang': target_lang,
            'source_lang': source_lang if source_lang else '',
            'model_provider': model_provider,
            'model_name': model_name,
            'temperature': temperature,
            'context': context if context else ''
        }
        
        response = requests.post(f"{API_BASE_URL}/api/v1/sessions/upload", files=files, data=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_session_content(session_id):
    """Get session content"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sessions/{session_id}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def chat_with_session(session_id, message):
    """Chat with translation agent"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/sessions/{session_id}/chat", 
                               json={"message": message})
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def prepare_download(session_id):
    """Prepare file for download"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/sessions/{session_id}/download")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_file(session_id):
    """Download translated file"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sessions/{session_id}/download-file")
        if response.status_code == 200:
            return response.content, response.headers.get('content-disposition', '').split('filename=')[-1].strip('"')
        return None, None
    except Exception as e:
        st.error(f"Download error: {str(e)}")
        return None, None

def list_sessions():
    """List all sessions"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sessions")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_content_preview(content, content_type):
    """Display content preview based on type"""
    if content_type == ".txt":
        if "text" in content:
            st.text_area("Nội dung gốc", content["text"], height=200, disabled=True)
    elif content_type == ".docx":
        if "paragraphs" in content:
            st.write("**Paragraphs:**")
            for i, para in enumerate(content["paragraphs"][:5]):  # Show first 5
                st.write(f"{i+1}. {para.get('text', '')}")
            if len(content["paragraphs"]) > 5:
                st.write(f"... và {len(content['paragraphs']) - 5} paragraphs khác")
    # Add more content types as needed

def get_content_preview(session_content):
    original_content = session_content.get("original_content", {})
    translated_content = session_content.get("translated_content", {})
    text_original = ""
    text_translated = ""
    for slide in original_content.get("slides", []):
        tmp = ""
        for shape in slide.get("shapes", []):
            for text_frame in shape.get("text_frames", []):
                tmp += text_frame.get("original_text", "")
                tmp += "\n"
        text_original += tmp + "\n\n"
    for slide in translated_content.get("slides", []):
        tmp = ""
        for shape in slide.get("shapes", []):
            for text_frame in shape.get("text_frames", []):
                tmp += text_frame.get("text", "")
                tmp += "\n"
        text_translated += tmp + "\n\n"

    return text_original, text_translated

def main():
    st.set_page_config(
        page_title="Translation Agent Chat",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("🌐 Translation Agent with Chat")
    st.markdown("Upload → Translate → Chat với Agent → Download")
    
    # Check API status
    api_status, api_info = check_api_status()
    
    if not api_status:
        st.error("⚠️ API Server không chạy! Vui lòng chạy: `python run_session_app.py`")
        st.stop()
    
    st.success("✅ API Server đang chạy")
    
    # Sidebar for upload and settings
    with st.sidebar:
        st.header("📁 Upload & Translate")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Chọn file để dịch",
            type=['txt', 'pdf', 'docx', 'pptx', 'xlsx'],
            help="Hỗ trợ: TXT, PDF, DOCX, PPTX, XLSX"
        )
        
        if uploaded_file is not None:
            st.success(f"📄 Đã chọn: {uploaded_file.name}")
        
        st.divider()
        
        st.header("⚙️ Cài đặt")
        
        # Translation settings
        target_lang = st.selectbox("Ngôn ngữ đích", ["vi", "en", "ja", "ko", "zh", "fr", "de"], index=0)
        source_lang = st.selectbox("Ngôn ngữ nguồn", ["auto", "en", "vi", "ja", "ko", "zh", "fr", "de"], index=0)
        
        # Model settings
        model_provider = st.selectbox("Model Provider", ["openai", "azure"], index=0)
        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], index=0)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
        
        # Context
        context = st.text_area("Context (tùy chọn)", placeholder="Ngữ cảnh dịch thuật...")
        
        # Upload button
        if uploaded_file is not None:
            if st.button("🚀 Upload và Dịch", type="primary", use_container_width=True):
                with st.spinner("Đang upload và dịch..."):
                    result = upload_and_create_session(
                        uploaded_file, target_lang, 
                        source_lang if source_lang != "auto" else None,
                        model_provider, model_name, temperature, context
                    )
                
                if result.get("success"):
                    st.success("✅ Dịch thành công!")
                    st.session_state.current_session_id = result["session_id"]
                    st.session_state.session_data = result
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {result.get('error', 'Unknown error')}")
        
        st.divider()
        
        # Session management
        st.header("📋 Sessions")
        if st.button("🔄 Refresh Sessions", use_container_width=True):
            st.rerun()
        
        sessions_data = list_sessions()
        if sessions_data.get("success") and sessions_data.get("sessions"):
            for session in sessions_data["sessions"][-5:]:  # Show last 5
                with st.expander(f"📄 {session['file_name'][:20]}..."):
                    st.write(f"**ID:** {session['session_id'][:8]}...")
                    st.write(f"**Created:** {session['created_at'][:19]}")
                    if st.button(f"Load Session", key=f"load_{session['session_id']}", use_container_width=True):
                        st.session_state.current_session_id = session['session_id']
                        st.rerun()
    
    # Main content area - Expand to full width for content and chat
    if hasattr(st.session_state, 'current_session_id'):
        # Session content area
        st.header("🎯 Nội dung Session")
        session_content = get_session_content(st.session_state.current_session_id)
        
        if session_content.get("success"):
            st.info(f"📋 Session: {st.session_state.current_session_id[:8]}...")
            
            # Content tabs with wider layout
            tab1, tab2 = st.tabs(["📝 Nội dung", "📊 Thông tin"])
            text_original, text_translated = get_content_preview(session_content)
            
            with tab1:
                # Use columns for better content layout
                content_col1, content_col2 = st.columns([1, 1])
                
                with content_col1:
                    st.write("**🌏 Nội dung gốc:**")
                    st.text_area("Nội dung gốc", text_original, height=300, disabled=True, key="original_content")
                
                with content_col2:
                    st.write("**🌐 Nội dung dịch:**")
                    st.text_area("Nội dung dịch", text_translated, height=300, disabled=True, key="translated_content")
            
            with tab2:
                st.json({
                    "file_name": session_content["file_name"],
                    "file_type": session_content["file_type"],
                    "source_lang": session_content["source_lang"],
                    "target_lang": session_content["target_lang"],
                    "model_used": session_content["model_used"],
                    "created_at": session_content["created_at"]
                })
        else:
            st.error(f"❌ Không thể tải session: {session_content.get('error')}")
    else:
        # Welcome message when no session is active
        st.header("🌐 Translation Agent with Chat")
        st.info("� Upload file từ sidebar để bắt đầu hoặc chọn session có sẵn")
        
        # Show some help information
        with st.container():
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("""
                ### 📁 Upload File
                - Chọn file từ sidebar
                - Hỗ trợ: TXT, PDF, DOCX, PPTX, XLSX
                - Tự động extract và dịch
                """)
            
            with col2:
                st.markdown("""
                ### 💬 Chat với Agent
                - Chỉnh sửa nội dung đã dịch
                - Cải thiện chất lượng dịch thuật
                - Tương tác real-time
                """)
            
            with col3:
                st.markdown("""
                ### 📥 Download
                - Reconstruction file với translation mới
                - Giữ nguyên format gốc
                - Tải về ngay lập tức
                """)
    
    # Chat section
    if hasattr(st.session_state, 'current_session_id'):
        st.divider()
        st.header("💬 Chat với Agent")
        
        # Chat history
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Nhập tin nhắn để chat với agent..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Agent đang suy nghĩ..."):
                    response = chat_with_session(st.session_state.current_session_id, prompt)
                if response.get("success"):
                    agent_response = response["response"]
                    st.write(agent_response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": agent_response})
                    if response.get("pending_changes", 0) > 0:
                        st.info(f"🔄 Có {response['pending_changes']} thay đổi đang chờ áp dụng")
                else:
                    error_msg = f"❌ Lỗi chat: {response.get('error')}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                # Reload session content and update preview after chat
                session_content = get_session_content(st.session_state.current_session_id)
                if session_content.get("success"):
                    text_original, text_translated = get_content_preview(session_content)
                    # Update the text areas by rerunning the app
                    st.session_state.text_original = text_original
                    st.session_state.text_translated = text_translated
                    st.rerun()
        
        # Download section
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📥 Chuẩn bị Download", type="secondary"):
                with st.spinner("Đang chuẩn bị file..."):
                    result = prepare_download(st.session_state.current_session_id)
                
                if result.get("success"):
                    st.success("✅ File đã sẵn sàng download!")
                    st.session_state.download_ready = True
                else:
                    st.error(f"❌ Lỗi: {result.get('error')}")
        
        with col2:
            if hasattr(st.session_state, 'download_ready') and st.session_state.download_ready:
                if st.button("📁 Download File", type="primary"):
                    file_content, filename = download_file(st.session_state.current_session_id)
                    
                    if file_content:
                        st.download_button(
                            label="💾 Tải về",
                            data=file_content,
                            file_name=filename or "translated_file.docx",
                            mime="application/octet-stream"
                        )
        
        with col3:
            if st.button("🗑️ Xóa Session"):
                try:
                    requests.delete(f"{API_BASE_URL}/api/v1/sessions/{st.session_state.current_session_id}")
                    del st.session_state.current_session_id
                    del st.session_state.chat_messages
                    if hasattr(st.session_state, 'download_ready'):
                        del st.session_state.download_ready
                    st.success("🗑️ Đã xóa session!")
                    st.rerun()
                except:
                    st.error("❌ Lỗi xóa session")

if __name__ == "__main__":
    main()
