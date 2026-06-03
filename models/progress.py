from datetime import date
from pydantic import BaseModel


class DailyProgress(BaseModel):
    date: date
    subject: str
    topic: str
    minutes_studied: int
    topics_covered: int = 0
    notes: str = ""


class ProgressReport(BaseModel):
    student_name: str
    report_date: date
    entries: list[DailyProgress] = []

    @property
    def total_minutes(self) -> int:
        return sum(e.minutes_studied for e in self.entries)

    @property
    def subjects_covered(self) -> set[str]:
        return {e.subject for e in self.entries}

    def get_weak_areas(self, threshold: float = 0.4) -> list[str]:
        from collections import Counter
        subject_time = Counter()
        for e in self.entries:
            subject_time[e.subject] += e.minutes_studied
        total = sum(subject_time.values()) or 1
        return [
            subj for subj, mins in subject_time.items()
            if mins / total < threshold
        ]
