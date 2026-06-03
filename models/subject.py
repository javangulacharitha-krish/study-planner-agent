from enum import Enum
from datetime import date
from pydantic import BaseModel


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Topic(BaseModel):
    name: str
    difficulty: Difficulty = Difficulty.MEDIUM
    estimated_hours: float = 1.0
    is_completed: bool = False


class Subject(BaseModel):
    name: str
    syllabus: list[Topic] = []
    exam_date: date | None = None
    priority: int = 1  # 1 = highest
    confidence_score: float = 0.5  # 0.0 (weak) to 1.0 (strong)

    @property
    def total_hours(self) -> float:
        return sum(t.estimated_hours for t in self.syllabus if not t.is_completed)

    @property
    def is_weak(self) -> bool:
        return self.confidence_score < 0.4

    @property
    def days_until_exam(self) -> int:
        if self.exam_date is None:
            return 999
        delta = (self.exam_date - date.today()).days
        return max(delta, 0)
