from datetime import time, date
from pydantic import BaseModel


class StudySession(BaseModel):
    subject: str
    topic: str
    start_time: time
    end_time: time
    duration_minutes: int
    is_completed: bool = False


class DayPlan(BaseModel):
    date: date
    sessions: list[StudySession] = []

    @property
    def total_study_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.sessions)

    @property
    def completed_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.sessions if s.is_completed)


class WeeklyPlan(BaseModel):
    week_start: date
    days: dict[str, DayPlan] = {}  # "Mon", "Tue", ...

    @property
    def total_study_hours(self) -> float:
        return sum(d.total_study_minutes for d in self.days.values()) / 60.0


class StudyPlan(BaseModel):
    student_name: str
    start_date: date
    end_date: date
    weekly_plans: list[WeeklyPlan] = []
    daily_target_hours: float = 4.0
