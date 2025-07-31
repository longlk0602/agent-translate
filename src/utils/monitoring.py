"""
Health check and monitoring for the translation agent
"""

import asyncio
from typing import Any, Dict

try:
    import psutil
except ImportError:
    psutil = None

from ..core.agent import TranslationAgent


class TranslationMonitor:
    """Monitor translation agent health and performance"""

    def __init__(self, agent: TranslationAgent):
        self.agent = agent
        self.start_time = asyncio.get_event_loop().time()
        self.health_checks = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""

        checks = {}

        # Check API connections
        checks["openai_available"] = (
            self.agent.translation_engine.openai_translator is not None
        )
        checks["azure_available"] = (
            self.agent.translation_engine.azure_translator is not None
        )

        # Check memory usage if psutil is available
        if psutil:
            process = psutil.Process()
            checks["memory_usage_mb"] = process.memory_info().rss / 1024 / 1024
        else:
            checks["memory_usage_mb"] = "N/A (psutil not installed)"

        # Check uptime
        checks["uptime_seconds"] = asyncio.get_event_loop().time() - self.start_time

        # Check cache size
        checks["cache_size"] = len(self.agent.translation_engine.translation_cache)

        # Check recent errors
        recent_errors = []
        for result in self.agent.translation_history[-10:]:
            recent_errors.extend(result.errors)
        checks["recent_errors"] = len(recent_errors)

        return {
            "status": "healthy" if checks["recent_errors"] < 5 else "degraded",
            "checks": checks,
            "timestamp": asyncio.get_event_loop().time(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""

        if not self.agent.translation_history:
            return {"message": "No metrics available"}

        processing_times = [
            result.processing_time for result in self.agent.translation_history
        ]
        word_counts = [result.word_count for result in self.agent.translation_history]

        return {
            "total_translations": len(self.agent.translation_history),
            "average_processing_time": sum(processing_times) / len(processing_times),
            "max_processing_time": max(processing_times),
            "min_processing_time": min(processing_times),
            "total_words_processed": sum(word_counts),
            "average_words_per_translation": sum(word_counts) / len(word_counts),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "error_rate": self._calculate_error_rate(),
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would need to be implemented with actual cache hit tracking
        return 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        if not self.agent.translation_history:
            return 0.0

        total_errors = sum(
            len(result.errors) for result in self.agent.translation_history
        )
        return total_errors / len(self.agent.translation_history)
