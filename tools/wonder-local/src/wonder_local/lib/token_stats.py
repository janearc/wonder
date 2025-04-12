from dataclasses import dataclass
from typing import Dict


@dataclass
class TokenStats:
    original_tokens: int
    processed_tokens: int
    reduction_ratio: float
    file_path: str


class TokenStatsTracker:
    def __init__(self):
        self.token_stats: Dict[str, TokenStats] = {}

    def estimate_tokens(self, text: str) -> int:
        # Very rough approximation of token count
        return len(text.split())

    def record(self, file_path: str, original: str, processed: str):
        original_tokens = self.estimate_tokens(original)
        processed_tokens = self.estimate_tokens(processed)
        reduction_ratio = (original_tokens - processed_tokens) / max(1, original_tokens)

        self.token_stats[file_path] = TokenStats(
            original_tokens=original_tokens,
            processed_tokens=processed_tokens,
            reduction_ratio=reduction_ratio,
            file_path=file_path
        )

    def summary(self):
        total_original = sum(s.original_tokens for s in self.token_stats.values())
        total_processed = sum(s.processed_tokens for s in self.token_stats.values())
        total_files = len(self.token_stats)
        avg_reduction = (
            (total_original - total_processed) / max(1, total_original) * 100
            if total_original else 0
        )
        return {
            "files_processed": total_files,
            "total_original_tokens": total_original,
            "total_processed_tokens": total_processed,
            "average_reduction_percent": avg_reduction,
        }

