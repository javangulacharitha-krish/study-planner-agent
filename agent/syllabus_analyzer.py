from models.subject import Subject, Topic, Difficulty


class SyllabusAnalyzer:
    """Analyzes syllabus to extract topics, difficulty, and identify weak areas."""

    @staticmethod
    def analyze(subjects: list[Subject]) -> dict:
        priorities = {}
        for s in subjects:
            urgency_score = min(1.0, 30.0 / max(s.days_until_exam, 1))
            weakness_score = 1.0 - s.confidence_score
            workload_score = min(1.0, s.total_hours / 20.0)
            priority = (urgency_score * 0.4 + weakness_score * 0.35 + workload_score * 0.25)
            priorities[s.name] = round(priority, 2)

        weak_subjects = [s for s in subjects if s.is_weak]
        hard_topics = [
            {"subject": s.name, "topic": t.name}
            for s in subjects for t in s.syllabus
            if t.difficulty == Difficulty.HARD and not t.is_completed
        ]

        return {
            "priorities": priorities,
            "weak_subjects": [s.name for s in weak_subjects],
            "hard_topics": hard_topics,
            "total_pending_hours": sum(s.total_hours for s in subjects),
            "sorted_subjects": sorted(subjects, key=lambda s: priorities.get(s.name, 0), reverse=True),
        }

    @staticmethod
    def estimate_hours_for_topic(topic: str, difficulty: Difficulty) -> float:
        mapping = {Difficulty.EASY: 0.5, Difficulty.MEDIUM: 1.5, Difficulty.HARD: 3.0}
        return mapping.get(difficulty, 1.0)
