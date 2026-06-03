from datetime import time
from models.subject import Topic, Difficulty


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def format_time(t: time) -> str:
    return t.strftime("%H:%M")


def day_name(weekday: int) -> str:
    return WEEKDAYS[weekday]


def group_topics_by_difficulty(topics: list[Topic]) -> dict:
    grouped = {d.value: [] for d in Difficulty}
    for t in topics:
        grouped[t.difficulty.value].append(t)
    return grouped
