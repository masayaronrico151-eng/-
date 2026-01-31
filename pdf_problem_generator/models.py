"""データモデル定義"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Difficulty(Enum):
    """難易度レベル"""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"

    @property
    def label_ja(self) -> str:
        labels = {
            "easy": "基本",
            "normal": "標準",
            "hard": "発展",
        }
        return labels[self.value]


@dataclass
class Problem:
    """抽出された問題"""
    number: int
    text: str
    subject: str = ""
    source_page: int = 0


@dataclass
class GeneratedProblem:
    """生成された類題"""
    original_number: int
    difficulty: Difficulty
    problem_text: str
    answer: str
    explanation: str


@dataclass
class ProblemSet:
    """問題セット（元問題 + 生成された類題群）"""
    original: Problem
    variants: list[GeneratedProblem] = field(default_factory=list)
