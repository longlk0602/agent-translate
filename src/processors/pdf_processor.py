"""
PDF document processor với hỗ trợ font tiếng Việt
"""

import copy
import os
from typing import Any, Dict, List

import fitz
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from processors.base import BaseDocumentProcessor


class PDFProcessor(BaseDocumentProcessor):
    """Processor for PDF documents với hỗ trợ font Unicode"""

    def __init__(self):
        super().__init__()
        # Danh sách các font Unicode hỗ trợ tiếng Việt
        self.unicode_fonts = [
            "Arial Unicode MS",
            "Times New Roman",
            "Tahoma",
            "Verdana",
            "DejaVu Sans",
            "Liberation Sans",
        ]

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from PDF while preserving structure"""
        doc = fitz.open(file_path)
        content = {"pages": []}

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_content = {"page_number": page_num + 1, "text_blocks": []}

            # Get text blocks with position information
            text_dict = page.get_text("dict")

            for block_idx, block in enumerate(text_dict["blocks"]):
                if "lines" in block:  # Text block
                    block_data = {
                        "block_index": block_idx,
                        "bbox": block["bbox"],  # Position information
                        "lines": [],
                    }

                    for line_idx, line in enumerate(block["lines"]):
                        line_text = ""
                        font_info = None

                        for span in line["spans"]:
                            line_text += span["text"]
                            if not font_info:
                                font_info = span

                        if line_text.strip():
                            block_data["lines"].append(
                                {
                                    "line_index": line_idx,
                                    "text": line_text.strip(),
                                    "original_text": line_text.strip(),
                                    "bbox": line["bbox"],
                                    "font_info": font_info,
                                }
                            )

                    if block_data["lines"]:
                        page_content["text_blocks"].append(block_data)

            content["pages"].append(page_content)

        doc.close()
        return content

    def _find_best_font(self, doc, preferred_size=12):
        """Tìm font tốt nhất hỗ trợ Unicode"""
        for font_name in self.unicode_fonts:
            try:
                # Thử load font
                font = fitz.Font(font_name)
                return font_name
            except:
                continue

        # Fallback: sử dụng font mặc định
        return "helv"  # Helvetica

    def reconstruct_document(
        self, original_path: str, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        """Reconstruct PDF by overlaying translated text on original"""
        original_doc = fitz.open(original_path)

        for page_data in translated_content["pages"]:
            page_num = page_data["page_number"] - 1
            if page_num >= len(original_doc):
                continue

            page = original_doc[page_num]

            # Remove original text blocks and add translated ones
            for block_data in page_data["text_blocks"]:
                # Clear original text area (white rectangle)
                bbox = fitz.Rect(block_data["bbox"])
                page.draw_rect(bbox, color=(1, 1, 1), fill=(1, 1, 1))

                # Add translated text với font Unicode
                y_offset = bbox.y0
                for line_data in block_data["lines"]:
                    if line_data["text"].strip():
                        font_size = 12
                        if line_data.get("font_info"):
                            font_size = line_data["font_info"].get("size", 12)

                        # Sử dụng font hỗ trợ Unicode
                        font_name = self._find_best_font(original_doc, font_size)

                        try:
                            page.insert_text(
                                (bbox.x0, y_offset + font_size),
                                line_data["text"],
                                fontsize=font_size,
                                fontname=font_name,
                                color=(0, 0, 0),
                                encoding=fitz.TEXT_ENCODING_UTF8,
                            )
                        except Exception as e:
                            print(f"Lỗi khi chèn text: {e}")
                            # Fallback: sử dụng font mặc định
                            page.insert_text(
                                (bbox.x0, y_offset + font_size),
                                line_data["text"],
                                fontsize=font_size,
                                color=(0, 0, 0),
                            )

                        y_offset += font_size + 2

        original_doc.save(output_path)
        original_doc.close()
        return output_path

    def reconstruct_with_reportlab(
        self, original_path: str, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        """Phương pháp thay thế sử dụng ReportLab để tạo PDF mới"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        # Đăng ký font tiếng Việt
        try:
            # Thử load font hệ thống
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/Windows/Fonts/arial.ttf",  # Windows
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "C:/Windows/Fonts/times.ttf",  # Windows Times New Roman
            ]

            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont("VietnameseFont", font_path))
                        font_registered = True
                        break
                    except:
                        continue

            if not font_registered:
                print("Không tìm thấy font Unicode, sử dụng font mặc định")

        except Exception as e:
            print(f"Lỗi khi đăng ký font: {e}")

        # Tạo PDF mới
        c = canvas.Canvas(output_path, pagesize=letter)

        for page_data in translated_content["pages"]:
            page_width, page_height = letter

            for block_data in page_data["text_blocks"]:
                bbox = block_data["bbox"]

                for line_data in block_data["lines"]:
                    if line_data["text"].strip():
                        font_size = 12
                        if line_data.get("font_info"):
                            font_size = line_data["font_info"].get("size", 12)

                        # Sử dụng font đã đăng ký
                        try:
                            c.setFont("VietnameseFont", font_size)
                        except:
                            c.setFont("Helvetica", font_size)

                        # Chuyển đổi tọa độ (PDF có gốc ở góc dưới trái)
                        y_pos = page_height - bbox[1] - font_size

                        c.drawString(bbox[0], y_pos, line_data["text"])

            c.showPage()

        c.save()
        return output_path

    def get_translatable_texts(self, extracted_content: Dict[str, Any]) -> List[str]:
        """Extract all translatable texts from PDF content"""
        texts = []
        for page_data in extracted_content["pages"]:
            for block_data in page_data["text_blocks"]:
                for line_data in block_data["lines"]:
                    if line_data["text"].strip():
                        texts.append(line_data["text"])
        return texts

    def apply_translations(
        self, extracted_content: Dict[str, Any], translations: List[str]
    ) -> Dict[str, Any]:
        """Apply translations to PDF content structure"""
        translated_content = copy.deepcopy(extracted_content)
        translation_idx = 0

        for page_data in translated_content["pages"]:
            for block_data in page_data["text_blocks"]:
                for line_data in block_data["lines"]:
                    if line_data["text"].strip() and translation_idx < len(
                        translations
                    ):
                        line_data["text"] = translations[translation_idx]
                        translation_idx += 1

        return translated_content

    def process_with_font_fallback(
        self, original_path: str, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        """Xử lý với fallback font strategy"""
        try:
            # Thử phương pháp 1: PyMuPDF với font Unicode
            return self.reconstruct_document(
                original_path, translated_content, output_path
            )
        except Exception as e:
            print(f"Phương pháp 1 thất bại: {e}")
            try:
                # Thử phương pháp 2: ReportLab
                return self.reconstruct_with_reportlab(
                    original_path, translated_content, output_path
                )
            except Exception as e2:
                print(f"Phương pháp 2 thất bại: {e2}")
                # Phương pháp 3: Tạo PDF text-only
                return self.create_text_only_pdf(translated_content, output_path)

    def get_pairs_translation(self, translated_content):
        return super().get_pairs_translation(translated_content)

    def create_text_only_pdf(
        self, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        """Tạo PDF chỉ có text đơn giản"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        for page_data in translated_content["pages"]:
            y_position = height - 50  # Bắt đầu từ trên xuống

            c.setFont("Helvetica", 12)
            c.drawString(50, y_position, f"Trang {page_data['page_number']}")
            y_position -= 30

            for block_data in page_data["text_blocks"]:
                for line_data in block_data["lines"]:
                    if line_data["text"].strip():
                        if y_position < 50:  # Nếu gần hết trang
                            c.showPage()
                            y_position = height - 50

                        # Chia text thành nhiều dòng nếu quá dài
                        text = line_data["text"]
                        max_width = width - 100

                        try:
                            c.setFont("Helvetica", 10)
                            c.drawString(50, y_position, text)
                        except:
                            # Nếu có ký tự đặc biệt không hiển thị được
                            safe_text = text.encode("ascii", "ignore").decode("ascii")
                            c.drawString(50, y_position, safe_text)

                        y_position -= 15

            c.showPage()

        c.save()
        return output_path
