"""Tests for the Study Planner Agent."""

from datetime import date
from models.subject import Subject, Topic, Difficulty
from models.progress import DailyProgress
from agent.syllabus_analyzer import SyllabusAnalyzer
from agent.scheduler import AdaptiveScheduler
from agent.tracker import ProgressTracker
from agent.planner_agent import StudyPlannerAgent


def make_sample_subjects() -> list[Subject]:
    return [
        Subject(
            name="Math",
            exam_date=date(2026, 7, 15),
            priority=1,
            confidence_score=0.3,
            syllabus=[
                Topic(name="Algebra", difficulty=Difficulty.HARD, estimated_hours=4.0),
                Topic(name="Calculus", difficulty=Difficulty.HARD, estimated_hours=5.0),
            ],
        ),
        Subject(
            name="Physics",
            exam_date=date(2026, 7, 20),
            priority=2,
            confidence_score=0.6,
            syllabus=[
                Topic(name="Mechanics", difficulty=Difficulty.MEDIUM, estimated_hours=3.0),
                Topic(name="Thermodynamics", difficulty=Difficulty.EASY, estimated_hours=2.0),
            ],
        ),
    ]


class TestSyllabusAnalyzer:
    def test_analyze_identifies_weak_subjects(self):
        subjects = make_sample_subjects()
        result = SyllabusAnalyzer.analyze(subjects)
        assert "Math" in result["weak_subjects"]
        assert "Physics" not in result["weak_subjects"]

    def test_analyze_prioritizes_urgent_weak_subjects(self):
        subjects = make_sample_subjects()
        result = SyllabusAnalyzer.analyze(subjects)
        assert result["priorities"]["Math"] > result["priorities"]["Physics"]

    def test_total_pending_hours(self):
        subjects = make_sample_subjects()
        result = SyllabusAnalyzer.analyze(subjects)
        assert result["total_pending_hours"] == 14.0


class TestAdaptiveScheduler:
    def test_generates_correct_number_of_weeks(self):
        subjects = make_sample_subjects()
        scheduler = AdaptiveScheduler(daily_target_hours=4.0)
        result = SyllabusAnalyzer.analyze(subjects)
        plan = scheduler.generate_plan(result["sorted_subjects"], date.today(), weeks=3)
        assert len(plan.weekly_plans) == 3

    def test_day_plan_has_sessions(self):
        subjects = make_sample_subjects()
        scheduler = AdaptiveScheduler()
        result = SyllabusAnalyzer.analyze(subjects)
        plan = scheduler.generate_plan(result["sorted_subjects"], date.today(), weeks=1)
        first_day = list(plan.weekly_plans[0].days.values())[0]
        assert len(first_day.sessions) > 0

    def test_sessions_have_valid_times(self):
        subjects = make_sample_subjects()
        scheduler = AdaptiveScheduler()
        result = SyllabusAnalyzer.analyze(subjects)
        plan = scheduler.generate_plan(result["sorted_subjects"], date.today(), weeks=1)
        for week in plan.weekly_plans:
            for day in week.days.values():
                for s in day.sessions:
                    assert s.start_time < s.end_time
                    assert s.duration_minutes > 0


class TestProgressTracker:
    def test_log_session_adds_entry(self):
        tracker = ProgressTracker()
        tracker.log_session("Math", "Algebra", 60)
        assert len(tracker.report.entries) == 1

    def test_update_confidence_boosts_studied_subjects(self):
        tracker = ProgressTracker()
        subjects = make_sample_subjects()
        tracker.log_session("Math", "Algebra", 120)
        updated = tracker.update_confidence(subjects)
        math = [s for s in updated if s.name == "Math"][0]
        assert math.confidence_score > 0.3

    def test_update_confidence_decays_unstudied_subjects(self):
        tracker = ProgressTracker()
        subjects = make_sample_subjects()
        tracker.log_session("Math", "Algebra", 60)
        updated = tracker.update_confidence(subjects)
        physics = [s for s in updated if s.name == "Physics"][0]
        assert physics.confidence_score < 0.6

    def test_study_streak(self):
        tracker = ProgressTracker()
        tracker.log_session("Math", "Algebra", 30)
        assert tracker.get_study_streak() >= 1


class TestStudyPlannerAgent:
    def test_full_pipeline(self, tmp_path):
        syllabus_path = tmp_path / "syllabus.json"
        import json
        syllabus_path.write_text(json.dumps({
            "subjects": [
                {
                    "name": "Math",
                    "exam_date": "2026-07-15",
                    "priority": 1,
                    "confidence_score": 0.3,
                    "topics": [
                        {"name": "Algebra", "difficulty": "hard", "estimated_hours": 4.0},
                    ],
                }
            ]
        }))

        agent = StudyPlannerAgent()
        agent.load_data(str(syllabus_path))
        analysis = agent.analyze()
        assert "Math" in analysis["weak_subjects"]

        plan = agent.generate_plan(weeks=2)
        assert len(plan.weekly_plans) == 2

        agent.log_study_session("Math", "Algebra", 60)
        summary = agent.get_progress_summary()
        assert summary["total_minutes"] >= 60

    def test_export_plan(self, tmp_path):
        syllabus_path = tmp_path / "syllabus.json"
        import json
        syllabus_path.write_text(json.dumps({
            "subjects": [
                {
                    "name": "Math",
                    "exam_date": "2026-07-15",
                    "priority": 1,
                    "confidence_score": 0.5,
                    "topics": [
                        {"name": "Algebra", "difficulty": "medium", "estimated_hours": 3.0},
                    ],
                }
            ]
        }))

        agent = StudyPlannerAgent()
        agent.load_data(str(syllabus_path))
        agent.generate_plan(weeks=1)

        output = tmp_path / "plan.json"
        agent.export_plan(str(output))
        assert output.exists()
