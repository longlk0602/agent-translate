"""
Gradio interface for session-based translation workflow
"""

import gradio as gr
import requests
import json
import tempfile
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"

class TranslationUI:
    def __init__(self):
        self.current_session_id = None
        self.chat_history = []
    
    def check_api_status(self):
        """Check if API server is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/")
            return True, "✅ API Server đang chạy"
        except requests.exceptions.ConnectionError:
            return False, "❌ API Server không chạy! Vui lòng chạy: python run_session_app.py"
    
    def upload_and_translate(self, file, target_lang, source_lang, model_provider, model_name, temperature, context):
        """Upload file and create translation session"""
        if file is None:
            return "❌ Vui lòng chọn file", "", "", ""
        
        try:
            # Read file
            with open(file.name, 'rb') as f:
                files = {'file': (Path(file.name).name, f, 'application/octet-stream')}
                data = {
                    'target_lang': target_lang,
                    'source_lang': source_lang if source_lang != "auto" else '',
                    'model_provider': model_provider,
                    'model_name': model_name,
                    'temperature': temperature,
                    'context': context if context else ''
                }
                
                response = requests.post(f"{API_BASE_URL}/api/v1/sessions/upload", files=files, data=data)
                result = response.json()
                print(result)
            if result.get("success"):
                self.current_session_id = result["session_id"]
                self.chat_history = []
                
                # Format response
                info = f"""
✅ **Dịch thành công!**
📋 **Session ID:** {result["session_id"][:8]}...
📄 **File:** {result["file_name"]}
🌐 **Ngôn ngữ:** {result["source_lang"]} → {result["target_lang"]}
🤖 **Model:** {result["model_used"]}
📝 **Số text:** {result["text_count"]}
⏱️ **Thời gian:** {result["processing_time"]:.2f}s
"""
                
                # Get content preview
                session_content = self.get_session_content()
                original_preview = self.format_content_preview(session_content.get("original_content", {}), "Nội dung gốc")
                translated_preview = self.format_content_preview(session_content.get("translated_content", {}), "Nội dung đã dịch")
                
                return info, original_preview, translated_preview, "💬 Session đã sẵn sàng! Bạn có thể chat với agent để chỉnh sửa bản dịch."
            else:
                return f"❌ Lỗi: {result.get('error', 'Unknown error')}", "", "", ""
                
        except Exception as e:
            return f"❌ Lỗi: {str(e)}", "", "", ""
    
    def get_session_content(self):
        """Get session content"""
        if not self.current_session_id:
            return {}
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/sessions/{self.current_session_id}")
            result = response.json()
            return result if result.get("success") else {}
        except:
            return {}
    
    def format_content_preview(self, content, title):
        """Format content for preview"""
        if not content:
            return f"**{title}:** Không có nội dung"
        
        preview = f"**{title}:**\n\n"
        
        if "text" in content:
            # TXT file
            text = content["text"][:500] + "..." if len(content["text"]) > 500 else content["text"]
            preview += f"```\n{text}\n```"
        
        elif "paragraphs" in content:
            # DOCX file
            preview += "**Paragraphs:**\n"
            for i, para in enumerate(content["paragraphs"][:3]):
                preview += f"{i+1}. {para.get('text', '')[:100]}...\n"
            if len(content["paragraphs"]) > 3:
                preview += f"... và {len(content['paragraphs']) - 3} paragraphs khác\n"
        
        elif "pages" in content:
            # PDF file
            preview += "**Pages:**\n"
            for i, page in enumerate(content["pages"][:2]):
                preview += f"Page {i+1}: {page.get('text', '')[:100]}...\n"
            if len(content["pages"]) > 2:
                preview += f"... và {len(content['pages']) - 2} pages khác\n"
        
        else:
            preview += "Định dạng file phức tạp - xem trong session details"
        
        return preview
    
    def chat_with_agent(self, message, history):
        """Chat with translation agent"""
        if not self.current_session_id:
            history.append([message, "❌ Không có session nào đang hoạt động. Vui lòng upload file trước."])
            return history, ""
        
        if not message.strip():
            return history, ""
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/v1/sessions/{self.current_session_id}/chat", 
                                   json={"message": message})
            result = response.json()
            
            if result.get("success"):
                agent_response = result["response"]
                if result.get("pending_changes", 0) > 0:
                    agent_response += f"\n\n🔄 *Có {result['pending_changes']} thay đổi đang chờ áp dụng*"
                
                history.append([message, agent_response])
            else:
                history.append([message, f"❌ Lỗi chat: {result.get('error')}"])
                
        except Exception as e:
            history.append([message, f"❌ Lỗi: {str(e)}"])
        
        return history, ""
    
    def prepare_download(self):
        """Prepare file for download"""
        if not self.current_session_id:
            return "❌ Không có session nào đang hoạt động."
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/v1/sessions/{self.current_session_id}/download")
            result = response.json()
            
            if result.get("success"):
                return f"✅ File đã sẵn sàng download!\n📁 Output: {result.get('file_name', 'translated_file')}"
            else:
                return f"❌ Lỗi: {result.get('error')}"
                
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"
    
    def download_file(self):
        """Download translated file"""
        if not self.current_session_id:
            return None, "❌ Không có session nào đang hoạt động."
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/sessions/{self.current_session_id}/download-file")
            
            if response.status_code == 200:
                # Save to temp file
                filename = response.headers.get('content-disposition', '').split('filename=')[-1].strip('"')
                if not filename:
                    filename = f"translated_file_{self.current_session_id[:8]}.docx"
                
                temp_path = f"/tmp/{filename}"
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                return temp_path, f"✅ File đã sẵn sàng tải về: {filename}"
            else:
                return None, f"❌ Lỗi download: {response.status_code}"
                
        except Exception as e:
            return None, f"❌ Lỗi: {str(e)}"
    
    def list_recent_sessions(self):
        """List recent sessions"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/sessions")
            result = response.json()
            
            if result.get("success") and result.get("sessions"):
                sessions_info = "📋 **Recent Sessions:**\n\n"
                for session in result["sessions"][-5:]:  # Last 5 sessions
                    sessions_info += f"• **{session['file_name']}** ({session['session_id'][:8]}...)\n"
                    sessions_info += f"  Created: {session['created_at'][:19]}\n\n"
                return sessions_info
            else:
                return "📋 Không có sessions nào."
                
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"

def create_interface():
    """Create Gradio interface"""
    ui = TranslationUI()
    
    with gr.Blocks(title="Translation Agent Chat", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🌐 Translation Agent with Chat
        **Upload → Translate → Chat với Agent → Download**
        """)
        
        # API Status check
        with gr.Row():
            status_btn = gr.Button("🔄 Check API Status", variant="secondary")
            status_output = gr.Markdown()
        
        status_btn.click(
            fn=lambda: ui.check_api_status()[1],
            outputs=status_output
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📁 Upload & Settings")
                
                # File upload
                file_input = gr.File(label="Chọn file để dịch", file_types=[".txt", ".pdf", ".docx", ".pptx", ".xlsx"])
                
                # Settings
                with gr.Row():
                    target_lang = gr.Dropdown(["vi", "en", "ja", "ko", "zh", "fr", "de"], value="vi", label="Ngôn ngữ đích")
                    source_lang = gr.Dropdown(["auto", "en", "vi", "ja", "ko", "zh", "fr", "de"], value="auto", label="Ngôn ngữ nguồn")
                
                with gr.Row():
                    model_provider = gr.Dropdown(["openai", "azure"], value="openai", label="Model Provider")
                    model_name = gr.Dropdown(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], value="gpt-4o-mini", label="Model")
                
                temperature = gr.Slider(0.0, 1.0, value=0.1, step=0.1, label="Temperature")
                context = gr.Textbox(label="Context (tùy chọn)", placeholder="Ngữ cảnh dịch thuật...")
                
                # Upload button
                upload_btn = gr.Button("🚀 Upload và Dịch", variant="primary", size="lg")
                
            with gr.Column(scale=1):
                gr.Markdown("## 📋 Session Info & Content")
                
                session_info = gr.Markdown()
                
                with gr.Tabs():
                    with gr.TabItem("🌏 Nội dung gốc"):
                        original_content = gr.Markdown()
                    
                    with gr.TabItem("🌐 Nội dung đã dịch"):
                        translated_content = gr.Markdown()
                    
                    with gr.TabItem("📊 Recent Sessions"):
                        sessions_list = gr.Markdown()
                        refresh_sessions_btn = gr.Button("🔄 Refresh", size="sm")
        
        # Chat section
        gr.Markdown("## 💬 Chat với Agent")
        chat_status = gr.Markdown()
        
        chatbot = gr.Chatbot(height=400, label="Chat với Translation Agent")
        chat_input = gr.Textbox(
            placeholder="Nhập tin nhắn để chat với agent... (VD: 'Thay AI thành trí tuệ nhân tạo')",
            label="Tin nhắn",
            lines=2
        )
        chat_btn = gr.Button("💬 Gửi", variant="primary")
        
        # Download section
        gr.Markdown("## 📥 Download")
        with gr.Row():
            prepare_btn = gr.Button("📋 Chuẩn bị Download", variant="secondary")
            download_btn = gr.Button("💾 Download File", variant="primary")
        
        download_status = gr.Markdown()
        download_file_output = gr.File(label="File đã dịch")
        
        # Event handlers
        upload_btn.click(
            fn=ui.upload_and_translate,
            inputs=[file_input, target_lang, source_lang, model_provider, model_name, temperature, context],
            outputs=[session_info, original_content, translated_content, chat_status]
        )
        
        chat_btn.click(
            fn=ui.chat_with_agent,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        chat_input.submit(
            fn=ui.chat_with_agent,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        prepare_btn.click(
            fn=ui.prepare_download,
            outputs=download_status
        )
        
        download_btn.click(
            fn=ui.download_file,
            outputs=[download_file_output, download_status]
        )
        
        refresh_sessions_btn.click(
            fn=ui.list_recent_sessions,
            outputs=sessions_list
        )
        
        # Auto-load sessions on startup
        interface.load(
            fn=ui.list_recent_sessions,
            outputs=sessions_list
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
