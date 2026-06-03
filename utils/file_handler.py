import json
from pathlib import Path
from models.subject import Subject, Topic, Difficulty
from models.progress import DailyProgress


class FileHandler:
    @staticmethod
    def load_subjects(path: str) -> list[Subject]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        subjects = []
        for item in data.get("subjects", []):
            topics = [Topic(**t) for t in item.get("topics", [])]
            subjects.append(Subject(**{k: v for k, v in item.items() if k != "topics"}, syllabus=topics))
        return subjects

    @staticmethod
    def load_progress(path: str) -> list[DailyProgress]:
        p = Path(path)
        if not p.exists():
            return []
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return [DailyProgress(**e) for e in data.get("progress", [])]

    @staticmethod
    def save_plan(path: str, plan_data: dict):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, indent=2, default=str)
