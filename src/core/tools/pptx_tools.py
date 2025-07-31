"""
Specialized tools for PPTX editing
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional

from core.tools.base import BaseTool

logger = logging.getLogger(__name__)


class PPTXSearchTool(BaseTool):
    """Tool to search text in PPTX content"""
    
    def __init__(self):
        super().__init__(
            name="search_pptx_text",
            description="Search for specific text in PowerPoint slides"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self, search_term: str, slide_idx: Optional[int] = None) -> Dict[str, Any]:
        """Search for text in PPTX content"""
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            results = []
            
            if "slides" not in content:
                return {
                    "success": False,
                    "error": "Invalid PPTX content structure"
                }
            
            slides_to_search = [content["slides"][slide_idx]] if slide_idx is not None else content["slides"]
            start_idx = slide_idx if slide_idx is not None else 0
            
            for slide_offset, slide in enumerate(slides_to_search):
                slide_idx_actual = start_idx + slide_offset
                slide_results = []
                
                for shape_idx, shape in enumerate(slide.get("shapes", [])):
                    for frame_idx, text_frame in enumerate(shape.get("text_frames", [])):
                        text = text_frame.get("translated_text", text_frame.get("original_text", ""))
                        
                        if search_term.lower() in text.lower():
                            slide_results.append({
                                "shape_idx": shape_idx,
                                "frame_idx": frame_idx,
                                "text": text,
                                "location": f"Slide {slide_idx_actual + 1}, Shape {shape_idx + 1}, Frame {frame_idx + 1}"
                            })
                
                if slide_results:
                    results.append({
                        "slide_idx": slide_idx_actual,
                        "slide_title": slide.get("title", f"Slide {slide_idx_actual + 1}"),
                        "matches": slide_results
                    })
            
            return {
                "success": True,
                "results": results,
                "total_matches": sum(len(slide["matches"]) for slide in results),
                "message": f"Found {sum(len(slide['matches']) for slide in results)} matches for '{search_term}'"
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
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "slide_idx": {
                        "type": "integer",
                        "description": "Optional: specific slide index to search (0-based), if not provided searches all slides"
                    }
                },
                "required": ["search_term"]
            }
        }


class PPTXReplaceTool(BaseTool):
    """Tool to replace text in PPTX content"""
    
    def __init__(self):
        super().__init__(
            name="replace_pptx_text",
            description="Replace specific text in PowerPoint slides"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self, old_text: str, new_text: str, slide_idx: Optional[int] = None) -> Dict[str, Any]:
        """Replace text in PPTX content"""
        logger.info(f"Replacing '{old_text}' with '{new_text}' in slide {slide_idx if slide_idx is not None else 'all'}")
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            
            if "slides" not in content:
                return {
                    "success": False,
                    "error": "Invalid PPTX content structure"
                }
            
            replacements = []
            slides_to_process = [slide_idx] if slide_idx is not None else range(len(content["slides"]))
            
            for s_idx in slides_to_process:
                if s_idx >= len(content["slides"]):
                    continue
                
                slide = content["slides"][s_idx]
                for shape_idx, shape in enumerate(slide.get("shapes", [])):                    
                    for frame_idx, text_frame in enumerate(shape.get("text_frames", [])):
                        # Check both translated_text and original_text
                        text_key = 'text'
                        if text_key in text_frame:
                            original_text = text_frame[text_key]
                            if re.search(re.escape(old_text), original_text, re.IGNORECASE):
                                # Sử dụng regex để thay thế không phân biệt hoa thường
                                pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                                new_full_text = pattern.sub(new_text, original_text)
                                text_frame[text_key] = new_full_text
                                replacements.append({
                                    "slide_idx": s_idx,
                                    "shape_idx": shape_idx,
                                    "frame_idx": frame_idx,
                                    "text_key": text_key,
                                    "old_text": original_text,
                                    "new_text": new_full_text,
                                    "location": f"Slide {s_idx + 1}, Shape {shape_idx + 1}, Frame {frame_idx + 1}"
                                })
            logger.info(f"Made {len(replacements)} replacements of '{old_text}' with '{new_text}'")
            return {
                "success": True,
                "replacements": replacements,
                "count": len(replacements),
                "updated_content": content,
                "message": f"Made {len(replacements)} replacements of '{old_text}' with '{new_text}'"
            }
            
        except Exception as e:
            logger.error(f"Replacement failed: {e}")
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
                    "old_text": {
                        "type": "string",
                        "description": "Text to replace"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text"
                    },
                    "slide_idx": {
                        "type": "integer",
                        "description": "Optional: specific slide index to replace in (0-based), if not provided replaces in all slides"
                    }
                },
                "required": ["old_text", "new_text"]
            }
        }


class PPTXAnalyzeTool(BaseTool):
    """Tool to analyze PPTX structure and content"""
    
    def __init__(self):
        super().__init__(
            name="analyze_pptx_structure",
            description="Analyze PowerPoint structure and provide content overview"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self) -> Dict[str, Any]:
        """Analyze PPTX structure"""
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            
            if "slides" not in content:
                return {
                    "success": False,
                    "error": "Invalid PPTX content structure"
                }
            
            analysis = {
                "total_slides": len(content["slides"]),
                "slides_overview": []
            }
            
            for slide_idx, slide in enumerate(content["slides"]):
                slide_info = {
                    "slide_number": slide_idx + 1,
                    "title": slide.get("title", f"Slide {slide_idx + 1}"),
                    "shapes_count": len(slide.get("shapes", [])),
                    "text_frames_count": 0,
                    "text_preview": []
                }
                
                for shape in slide.get("shapes", []):
                    text_frames = shape.get("text_frames", [])
                    slide_info["text_frames_count"] += len(text_frames)
                    
                    for text_frame in text_frames:
                        text = text_frame.get("translated_text", text_frame.get("original_text", ""))
                        if text.strip():
                            preview = text[:100] + "..." if len(text) > 100 else text
                            slide_info["text_preview"].append(preview)
                
                analysis["slides_overview"].append(slide_info)
            
            # Summary statistics
            total_text_frames = sum(slide["text_frames_count"] for slide in analysis["slides_overview"])
            total_shapes = sum(slide["shapes_count"] for slide in analysis["slides_overview"])
            
            analysis["summary"] = {
                "total_slides": analysis["total_slides"],
                "total_shapes": total_shapes,
                "total_text_frames": total_text_frames,
                "avg_shapes_per_slide": round(total_shapes / max(1, analysis["total_slides"]), 2),
                "avg_text_frames_per_slide": round(total_text_frames / max(1, analysis["total_slides"]), 2)
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "message": f"Analyzed {analysis['total_slides']} slides with {total_shapes} shapes and {total_text_frames} text frames"
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
                "properties": {},
                "required": []
            }
        }


class PPTXSlideInfoTool(BaseTool):
    """Tool to get detailed information about a specific slide"""
    
    def __init__(self):
        super().__init__(
            name="get_pptx_slide_info",
            description="Get detailed information about a specific PowerPoint slide"
        )
        self.session_content = None
    
    def set_session_content(self, content: Dict[str, Any]):
        """Set the session content for this tool"""
        self.session_content = content
    
    async def execute(self, slide_idx: int) -> Dict[str, Any]:
        """Get detailed slide information"""
        try:
            if not self.session_content:
                return {
                    "success": False,
                    "error": "No session content available"
                }
            
            content = self.session_content
            
            if "slides" not in content:
                return {
                    "success": False,
                    "error": "Invalid PPTX content structure"
                }
            
            if slide_idx >= len(content["slides"]) or slide_idx < 0:
                return {
                    "success": False,
                    "error": f"Slide index {slide_idx} out of range (0-{len(content['slides'])-1})"
                }
            
            slide = content["slides"][slide_idx]
            
            slide_info = {
                "slide_number": slide_idx + 1,
                "slide_index": slide_idx,
                "title": slide.get("title", f"Slide {slide_idx + 1}"),
                "shapes": []
            }
            
            for shape_idx, shape in enumerate(slide.get("shapes", [])):
                shape_info = {
                    "shape_index": shape_idx,
                    "shape_type": shape.get("type", "unknown"),
                    "text_frames": []
                }
                
                for frame_idx, text_frame in enumerate(shape.get("text_frames", [])):
                    frame_info = {
                        "frame_index": frame_idx,
                        "original_text": text_frame.get("original_text", ""),
                        "translated_text": text_frame.get("translated_text", ""),
                        "text": text_frame.get("text", ""),
                        "char_count": len(text_frame.get("translated_text", text_frame.get("original_text", "")))
                    }
                    shape_info["text_frames"].append(frame_info)
                
                slide_info["shapes"].append(shape_info)
            
            return {
                "success": True,
                "slide_info": slide_info,
                "message": f"Retrieved info for slide {slide_idx + 1}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get slide info: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "slide_idx": {
                        "type": "integer",
                        "description": "Slide index (0-based) to get information for"
                    }
                },
                "required": ["slide_idx"]
            }
        }
