"""
Specialized tools for Excel/XLSX editing
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from core.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ExcelSearchTool(BaseTool):
    """Tool to search text in Excel content"""
    
    def __init__(self):
        super().__init__(
            name="search_excel_text",
            description="Search for specific text in Excel spreadsheet"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self, search_term: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Search for text in Excel content"""
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            results = []
            
            if "sheets" not in content:
                return {
                    "success": False,
                    "error": "Invalid Excel content structure"
                }
            
            sheets_to_search = content["sheets"]
            if sheet_name:
                sheets_to_search = [sheet for sheet in content["sheets"] if sheet.get("name") == sheet_name]
                if not sheets_to_search:
                    return {
                        "success": False,
                        "error": f"Sheet '{sheet_name}' not found"
                    }
            
            for sheet_idx, sheet in enumerate(sheets_to_search):
                sheet_name_actual = sheet.get("name", f"Sheet{sheet_idx + 1}")
                
                for row_idx, row in enumerate(sheet.get("cells", [])):
                    for col_idx, cell in enumerate(row):
                        cell_value = str(cell.get("value", ""))
                        
                        if search_term.lower() in cell_value.lower():
                            # Convert column index to Excel column letter
                            col_letter = self._num_to_excel_col(col_idx)
                            
                            results.append({
                                "sheet_index": sheet_idx,
                                "sheet_name": sheet_name_actual,
                                "row_index": row_idx,
                                "col_index": col_idx,
                                "cell_address": f"{col_letter}{row_idx + 1}",
                                "value": cell_value,
                                "location": f"Sheet '{sheet_name}', Cell {col_letter}{row_idx + 1}"
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
    
    def _num_to_excel_col(self, col_num: int) -> str:
        """Convert column number to Excel column letter"""
        result = ""
        while col_num >= 0:
            result = chr(col_num % 26 + ord('A')) + result
            col_num = col_num // 26 - 1
            if col_num < 0:
                break
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Optional: specific sheet name to search in, if not provided searches all sheets"
                    }
                },
                "required": ["search_term"]
            }
        }


class ExcelReplaceTool(BaseTool):
    """Tool to replace text in Excel content"""
    
    def __init__(self):
        super().__init__(
            name="replace_excel_text",
            description="Replace specific text in Excel spreadsheet"
        )
    
    async def execute(self, content: Dict[str, Any], old_text: str, new_text: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Replace text in Excel content"""
        try:
            if "sheets" not in content:
                return {
                    "success": False,
                    "error": "Invalid Excel content structure"
                }
            
            replacements = []
            
            for sheet_idx, sheet in enumerate(content["sheets"]):
                current_sheet_name = sheet.get("name", f"Sheet{sheet_idx + 1}")
                
                # Skip if specific sheet requested and this isn't it
                if sheet_name and current_sheet_name != sheet_name:
                    continue
                
                for row_idx, row in enumerate(sheet.get("cells", [])):
                    for col_idx, cell in enumerate(row):
                        cell_value = str(cell.get("value", ""))
                        
                        if old_text in cell_value:
                            old_value = cell_value
                            new_value = cell_value.replace(old_text, new_text)
                            cell["value"] = new_value
                            
                            col_letter = self._num_to_excel_col(col_idx)
                            
                            replacements.append({
                                "sheet_index": sheet_idx,
                                "sheet_name": current_sheet_name,
                                "row_index": row_idx,
                                "col_index": col_idx,
                                "cell_address": f"{col_letter}{row_idx + 1}",
                                "old_value": old_value,
                                "new_value": new_value,
                                "location": f"Sheet '{current_sheet_name}', Cell {col_letter}{row_idx + 1}"
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
    
    def _num_to_excel_col(self, col_num: int) -> str:
        """Convert column number to Excel column letter"""
        result = ""
        while col_num >= 0:
            result = chr(col_num % 26 + ord('A')) + result
            col_num = col_num // 26 - 1
            if col_num < 0:
                break
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "Excel content structure"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Text to replace"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Specific sheet name to replace in (optional)"
                    }
                },
                "required": ["content", "old_text", "new_text"]
            }
        }


class ExcelAnalyzeTool(BaseTool):
    """Tool to analyze Excel structure and content"""
    
    def __init__(self):
        super().__init__(
            name="analyze_excel_structure",
            description="Analyze Excel spreadsheet structure and provide content overview"
        )
    
    async def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Excel structure"""
        try:
            if "sheets" not in content:
                return {
                    "success": False,
                    "error": "Invalid Excel content structure"
                }
            
            analysis = {
                "total_sheets": len(content["sheets"]),
                "sheets_overview": []
            }
            
            total_cells = 0
            total_non_empty_cells = 0
            
            for sheet_idx, sheet in enumerate(content["sheets"]):
                sheet_name = sheet.get("name", f"Sheet{sheet_idx + 1}")
                rows = sheet.get("cells", [])
                
                sheet_info = {
                    "sheet_index": sheet_idx,
                    "sheet_name": sheet_name,
                    "rows_count": len(rows),
                    "columns_count": max(len(row) for row in rows) if rows else 0,
                    "total_cells": sum(len(row) for row in rows),
                    "non_empty_cells": 0,
                    "data_types": {}
                }
                
                # Analyze cell contents
                for row in rows:
                    for cell in row:
                        value = cell.get("value", "")
                        if value and str(value).strip():
                            sheet_info["non_empty_cells"] += 1
                            
                            # Basic data type detection
                            value_str = str(value)
                            if value_str.isdigit():
                                sheet_info["data_types"]["number"] = sheet_info["data_types"].get("number", 0) + 1
                            elif "." in value_str and value_str.replace(".", "").isdigit():
                                sheet_info["data_types"]["decimal"] = sheet_info["data_types"].get("decimal", 0) + 1
                            else:
                                sheet_info["data_types"]["text"] = sheet_info["data_types"].get("text", 0) + 1
                
                total_cells += sheet_info["total_cells"]
                total_non_empty_cells += sheet_info["non_empty_cells"]
                
                analysis["sheets_overview"].append(sheet_info)
            
            # Summary statistics
            analysis["summary"] = {
                "total_sheets": analysis["total_sheets"],
                "total_cells": total_cells,
                "total_non_empty_cells": total_non_empty_cells,
                "data_density": round(total_non_empty_cells / max(1, total_cells) * 100, 2)
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "message": f"Analyzed {analysis['total_sheets']} sheets with {total_cells} total cells ({total_non_empty_cells} non-empty)"
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
                        "description": "Excel content structure"
                    }
                },
                "required": ["content"]
            }
        }


class ExcelGetRangeTool(BaseTool):
    """Tool to get content from specific range in Excel"""
    
    def __init__(self):
        super().__init__(
            name="get_excel_range",
            description="Get content from specific range in Excel spreadsheet"
        )
    
    async def execute(self, content: Dict[str, Any], sheet_name: str, start_row: int, end_row: int, start_col: int, end_col: int) -> Dict[str, Any]:
        """Get content from Excel range"""
        try:
            if "sheets" not in content:
                return {
                    "success": False,
                    "error": "Invalid Excel content structure"
                }
            
            # Find the sheet
            target_sheet = None
            for sheet in content["sheets"]:
                if sheet.get("name") == sheet_name:
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                return {
                    "success": False,
                    "error": f"Sheet '{sheet_name}' not found"
                }
            
            range_data = []
            rows = target_sheet.get("cells", [])
            
            for row_idx in range(start_row, min(end_row + 1, len(rows))):
                row_data = []
                row = rows[row_idx]
                
                for col_idx in range(start_col, min(end_col + 1, len(row))):
                    cell = row[col_idx] if col_idx < len(row) else {}
                    row_data.append({
                        "row": row_idx,
                        "col": col_idx,
                        "address": f"{self._num_to_excel_col(col_idx)}{row_idx + 1}",
                        "value": cell.get("value", "")
                    })
                
                range_data.append(row_data)
            
            start_addr = f"{self._num_to_excel_col(start_col)}{start_row + 1}"
            end_addr = f"{self._num_to_excel_col(end_col)}{end_row + 1}"
            
            return {
                "success": True,
                "range_data": range_data,
                "range_address": f"{start_addr}:{end_addr}",
                "sheet_name": sheet_name,
                "message": f"Retrieved range {start_addr}:{end_addr} from sheet '{sheet_name}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get range: {str(e)}"
            }
    
    def _num_to_excel_col(self, col_num: int) -> str:
        """Convert column number to Excel column letter"""
        result = ""
        while col_num >= 0:
            result = chr(col_num % 26 + ord('A')) + result
            col_num = col_num // 26 - 1
            if col_num < 0:
                break
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "Excel content structure"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Sheet name"
                    },
                    "start_row": {
                        "type": "integer",
                        "description": "Start row index (0-based)"
                    },
                    "end_row": {
                        "type": "integer",
                        "description": "End row index (0-based)"
                    },
                    "start_col": {
                        "type": "integer",
                        "description": "Start column index (0-based)"
                    },
                    "end_col": {
                        "type": "integer",
                        "description": "End column index (0-based)"
                    }
                },
                "required": ["content", "sheet_name", "start_row", "end_row", "start_col", "end_col"]
            }
        }
