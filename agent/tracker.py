from datetime import date
from models.subject import Subject
from models.progress import DailyProgress, ProgressReport


class ProgressTracker:
    """Tracks daily progress and updates subject confidence scores."""

    def __init__(self):
        self.report = ProgressReport(student_name="Student", report_date=date.today())

    def log_session(
        self,
        subject_name: str,
        topic: str,
        minutes: int,
        topics_covered: int = 0,
        notes: str = "",
    ):
        entry = DailyProgress(
            date=date.today(),
            subject=subject_name,
            topic=topic,
            minutes_studied=minutes,
            topics_covered=topics_covered or 1,
            notes=notes,
        )
        self.report.entries.append(entry)
        return entry

    def update_confidence(self, subjects: list[Subject]) -> list[Subject]:
        today_entries = [e for e in self.report.entries if e.date == date.today()]
        studied_today = {e.subject for e in today_entries}

        for subj in subjects:
            if subj.name in studied_today:
                total_mins = sum(
                    e.minutes_studied for e in today_entries if e.subject == subj.name
                )
                boost = min(0.1, total_mins / 120.0 * 0.1)
                subj.confidence_score = min(1.0, subj.confidence_score + boost)
            else:
                decay = 0.02
                subj.confidence_score = max(0.0, subj.confidence_score - decay)

        return subjects

    def get_study_streak(self) -> int:
        streak = 0
        seen_dates = sorted({e.date for e in self.report.entries}, reverse=True)
        from datetime import timedelta

        for i, d in enumerate(seen_dates):
            if i == 0:
                streak = 1
            elif (seen_dates[i - 1] - d).days == 1:
                streak += 1
            else:
                break
        return streak

    def weekly_summary(self) -> dict:
        from collections import Counter
        today = date.today()
        week_entries = [
            e for e in self.report.entries
            if (today - e.date).days < 7
        ]
        subject_mins = Counter()
        for e in week_entries:
            subject_mins[e.subject] += e.minutes_studied
        return {
            "total_minutes": sum(subject_mins.values()),
            "per_subject": dict(subject_mins),
            "streak": self.get_study_streak(),
            "days_active": len({e.date for e in week_entries}),
        }
