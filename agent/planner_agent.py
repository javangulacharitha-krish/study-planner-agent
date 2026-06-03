from datetime import date
from models.subject import Subject
from models.study_plan import StudyPlan
from agent.syllabus_analyzer import SyllabusAnalyzer
from agent.scheduler import AdaptiveScheduler
from agent.tracker import ProgressTracker
from utils.file_handler import FileHandler


class StudyPlannerAgent:
    """Orchestrator agent that coordinates analysis, scheduling, and tracking."""

    def __init__(self, daily_target_hours: float = 4.0):
        self.analyzer = SyllabusAnalyzer()
        self.scheduler = AdaptiveScheduler(daily_target_hours)
        self.tracker = ProgressTracker()
        self.subjects: list[Subject] = []
        self.current_plan: StudyPlan | None = None

    def load_data(self, syllabus_path: str, progress_path: str | None = None):
        self.subjects = FileHandler.load_subjects(syllabus_path)
        if progress_path:
            entries = FileHandler.load_progress(progress_path)
            self.tracker.report.entries.extend(entries)

    def analyze(self) -> dict:
        return self.analyzer.analyze(self.subjects)

    def generate_plan(self, weeks: int = 4) -> StudyPlan:
        analysis = self.analyze()
        done_topics = [
            f"{e.subject}:{e.topic}"
            for e in self.tracker.report.entries
        ]
        self.current_plan = self.scheduler.generate_plan(
            sorted_subjects=analysis["sorted_subjects"],
            start_date=date.today(),
            weeks=weeks,
            previous_progress=done_topics,
        )
        return self.current_plan

    def log_study_session(
        self,
        subject_name: str,
        topic: str,
        minutes: int,
        topics_covered: int = 0,
        notes: str = "",
    ):
        self.tracker.log_session(subject_name, topic, minutes, topics_covered, notes)
        self.subjects = self.tracker.update_confidence(self.subjects)

    def get_progress_summary(self) -> dict:
        analysis = self.analyze()
        summary = self.tracker.weekly_summary()
        return {
            **summary,
            "weak_subjects": analysis["weak_subjects"],
            "hard_topics": analysis["hard_topics"],
            "total_pending_hours": analysis["total_pending_hours"],
        }

    def export_plan(self, path: str):
        if not self.current_plan:
            raise ValueError("No plan generated yet. Call generate_plan() first.")
        plan_data = {
            "student": self.current_plan.student_name,
            "start": str(self.current_plan.start_date),
            "end": str(self.current_plan.end_date),
            "daily_target_hours": self.current_plan.daily_target_hours,
            "weeks": [],
        }
        for wp in self.current_plan.weekly_plans:
            week_data = {"week_start": str(wp.week_start), "days": {}}
            for day_name, day_plan in wp.days.items():
                week_data["days"][day_name] = {
                    "date": str(day_plan.date),
                    "total_minutes": day_plan.total_study_minutes,
                    "sessions": [
                        {
                            "subject": s.subject,
                            "topic": s.topic,
                            "start": str(s.start_time),
                            "end": str(s.end_time),
                            "duration": s.duration_minutes,
                        }
                        for s in day_plan.sessions
                    ],
                }
            plan_data["weeks"].append(week_data)
        FileHandler.save_plan(path, plan_data)
