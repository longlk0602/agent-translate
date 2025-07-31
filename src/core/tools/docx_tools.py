"""
Specialized tools for DOCX editing
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from core.tools.base import BaseTool

logger = logging.getLogger(__name__)


class DOCXSearchTool(BaseTool):
    """Tool to search text in DOCX content"""
    
    def __init__(self):
        super().__init__(
            name="search_docx_text",
            description="Search for specific text in Word document"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self, search_term: str) -> Dict[str, Any]:
        """Search for text in DOCX content"""
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            results = []
            
            # Search in paragraphs
            if "paragraphs" in content:
                for para_idx, paragraph in enumerate(content["paragraphs"]):
                    text = paragraph.get("text", "")
                    if search_term.lower() in text.lower():
                        results.append({
                            "type": "paragraph",
                            "index": para_idx,
                            "text": text,
                            "location": f"Paragraph {para_idx + 1}"
                        })
            
            # Search in tables
            if "tables" in content:
                for table_idx, table in enumerate(content["tables"]):
                    for row_idx, row in enumerate(table.get("rows", [])):
                        for cell_idx, cell in enumerate(row.get("cells", [])):
                            text = cell.get("text", "")
                            if search_term.lower() in text.lower():
                                results.append({
                                    "type": "table_cell",
                                    "table_index": table_idx,
                                    "row_index": row_idx,
                                    "cell_index": cell_idx,
                                    "text": text,
                                    "location": f"Table {table_idx + 1}, Row {row_idx + 1}, Cell {cell_idx + 1}"
                                })
            
            # Search in headers
            if "headers" in content:
                for header_idx, header in enumerate(content["headers"]):
                    text = header.get("text", "")
                    if search_term.lower() in text.lower():
                        results.append({
                            "type": "header",
                            "index": header_idx,
                            "text": text,
                            "location": f"Header {header_idx + 1}"
                        })
            
            # Search in footers
            if "footers" in content:
                for footer_idx, footer in enumerate(content["footers"]):
                    text = footer.get("text", "")
                    if search_term.lower() in text.lower():
                        results.append({
                            "type": "footer",
                            "index": footer_idx,
                            "text": text,
                            "location": f"Footer {footer_idx + 1}"
                        })
            
            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "message": f"Found {len(results)} matches for '{search_term}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "DOCX content structure"
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for"
                    }
                },
                "required": ["content", "search_term"]
            }
        }


class DOCXReplaceTool(BaseTool):
    """Tool to replace text in DOCX content"""
    
    def __init__(self):
        super().__init__(
            name="replace_docx_text",
            description="Replace specific text in Word document"
        )
    
    async def execute(self, content: Dict[str, Any], old_text: str, new_text: str, location_type: Optional[str] = None) -> Dict[str, Any]:
        """Replace text in DOCX content"""
        try:
            replacements = []
            
            # Replace in paragraphs
            if "paragraphs" in content and (not location_type or location_type == "paragraph"):
                for para_idx, paragraph in enumerate(content["paragraphs"]):
                    if old_text in paragraph.get("text", ""):
                        old_full_text = paragraph["text"]
                        paragraph["text"] = old_full_text.replace(old_text, new_text)
                        
                        # Also update runs if they exist
                        for run in paragraph.get("runs", []):
                            if old_text in run.get("text", ""):
                                run["text"] = run["text"].replace(old_text, new_text)
                        
                        replacements.append({
                            "type": "paragraph",
                            "index": para_idx,
                            "old_text": old_full_text,
                            "new_text": paragraph["text"],
                            "location": f"Paragraph {para_idx + 1}"
                        })
            
            # Replace in tables
            if "tables" in content and (not location_type or location_type == "table"):
                for table_idx, table in enumerate(content["tables"]):
                    for row_idx, row in enumerate(table.get("rows", [])):
                        for cell_idx, cell in enumerate(row.get("cells", [])):
                            if old_text in cell.get("text", ""):
                                old_cell_text = cell["text"]
                                cell["text"] = old_cell_text.replace(old_text, new_text)
                                
                                replacements.append({
                                    "type": "table_cell",
                                    "table_index": table_idx,
                                    "row_index": row_idx,
                                    "cell_index": cell_idx,
                                    "old_text": old_cell_text,
                                    "new_text": cell["text"],
                                    "location": f"Table {table_idx + 1}, Row {row_idx + 1}, Cell {cell_idx + 1}"
                                })
            
            # Replace in headers
            if "headers" in content and (not location_type or location_type == "header"):
                for header_idx, header in enumerate(content["headers"]):
                    if old_text in header.get("text", ""):
                        old_header_text = header["text"]
                        header["text"] = old_header_text.replace(old_text, new_text)
                        
                        replacements.append({
                            "type": "header",
                            "index": header_idx,
                            "old_text": old_header_text,
                            "new_text": header["text"],
                            "location": f"Header {header_idx + 1}"
                        })
            
            # Replace in footers
            if "footers" in content and (not location_type or location_type == "footer"):
                for footer_idx, footer in enumerate(content["footers"]):
                    if old_text in footer.get("text", ""):
                        old_footer_text = footer["text"]
                        footer["text"] = old_footer_text.replace(old_text, new_text)
                        
                        replacements.append({
                            "type": "footer",
                            "index": footer_idx,
                            "old_text": old_footer_text,
                            "new_text": footer["text"],
                            "location": f"Footer {footer_idx + 1}"
                        })
            
            return {
                "success": True,
                "replacements": replacements,
                "count": len(replacements),
                "updated_content": content,
                "message": f"Made {len(replacements)} replacements of '{old_text}' with '{new_text}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Replacement failed: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "DOCX content structure"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Text to replace"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text"
                    },
                    "location_type": {
                        "type": "string",
                        "enum": ["paragraph", "table", "header", "footer"],
                        "description": "Specific location type to replace in (optional)"
                    }
                },
                "required": ["content", "old_text", "new_text"]
            }
        }


class DOCXAnalyzeTool(BaseTool):
    """Tool to analyze DOCX structure and content"""
    
    def __init__(self):
        super().__init__(
            name="analyze_docx_structure",
            description="Analyze Word document structure and provide content overview"
        )
    
    async def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DOCX structure"""
        try:
            analysis = {
                "paragraphs_count": len(content.get("paragraphs", [])),
                "tables_count": len(content.get("tables", [])),
                "headers_count": len(content.get("headers", [])),
                "footers_count": len(content.get("footers", [])),
                "content_overview": {}
            }
            
            # Analyze paragraphs
            if "paragraphs" in content:
                para_analysis = []
                for para_idx, paragraph in enumerate(content["paragraphs"]):
                    text = paragraph.get("text", "")
                    para_analysis.append({
                        "index": para_idx,
                        "char_count": len(text),
                        "word_count": len(text.split()) if text else 0,
                        "preview": text[:100] + "..." if len(text) > 100 else text
                    })
                analysis["content_overview"]["paragraphs"] = para_analysis
            
            # Analyze tables
            if "tables" in content:
                table_analysis = []
                for table_idx, table in enumerate(content["tables"]):
                    rows = table.get("rows", [])
                    table_analysis.append({
                        "index": table_idx,
                        "rows_count": len(rows),
                        "columns_count": len(rows[0].get("cells", [])) if rows else 0,
                        "total_cells": sum(len(row.get("cells", [])) for row in rows)
                    })
                analysis["content_overview"]["tables"] = table_analysis
            
            # Calculate totals
            total_words = 0
            total_chars = 0
            
            for para in content.get("paragraphs", []):
                text = para.get("text", "")
                total_words += len(text.split()) if text else 0
                total_chars += len(text)
            
            analysis["summary"] = {
                "total_words": total_words,
                "total_characters": total_chars,
                "document_sections": {
                    "paragraphs": analysis["paragraphs_count"],
                    "tables": analysis["tables_count"],
                    "headers": analysis["headers_count"],
                    "footers": analysis["footers_count"]
                }
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "message": f"Analyzed document: {total_words} words, {analysis['paragraphs_count']} paragraphs, {analysis['tables_count']} tables"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "DOCX content structure"
                    }
                },
                "required": ["content"]
            }
        }
