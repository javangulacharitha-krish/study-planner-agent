from datetime import date, time, timedelta
import random
from models.subject import Subject, Difficulty
from models.study_plan import StudyPlan, WeeklyPlan, DayPlan, StudySession
from utils.helpers import WEEKDAYS


class AdaptiveScheduler:
    """Generates adaptive weekly study plans based on syllabus analysis and progress."""

    def __init__(self, daily_target_hours: float = 4.0):
        self.daily_target_hours = daily_target_hours

    def generate_plan(
        self,
        sorted_subjects: list[Subject],
        start_date: date,
        weeks: int = 4,
        previous_progress: list[str] | None = None,
    ) -> StudyPlan:
        plan = StudyPlan(
            student_name="Student",
            start_date=start_date,
            end_date=start_date + timedelta(weeks=weeks),
            daily_target_hours=self.daily_target_hours,
        )

        done_topics = set(previous_progress or [])
        hours_per_week = self.daily_target_hours * 7

        all_pending = []
        for s in sorted_subjects:
            for t in s.syllabus:
                key = f"{s.name}:{t.name}"
                if key not in done_topics and not t.is_completed:
                    all_pending.append((s, t, key))

        all_topics_keys = set()
        for s in sorted_subjects:
            for t in s.syllabus:
                all_topics_keys.add(f"{s.name}:{t.name}")

        total_hours = sum(t.estimated_hours for _, t, _ in all_pending)
        new_material_weeks = max(1, round(total_hours / hours_per_week))

        for week_idx in range(weeks):
            week_start = start_date + timedelta(weeks=week_idx)
            weekly = WeeklyPlan(week_start=week_start)
            week_topic_keys = set()
            review_keys = set()

            if all_pending:
                batch_size = max(1, len(all_pending) // max(new_material_weeks - week_idx, 1))
                week_new = all_pending[:batch_size]
                all_pending = all_pending[batch_size:]
                week_topic_keys = {key for _, _, key in week_new}

                # Mix in review of previously completed topics
                available_for_review = list(done_topics - week_topic_keys)
                if available_for_review:
                    review_keys.update(random.sample(available_for_review, min(2, len(available_for_review))))
            else:
                # All new material covered -- only review
                available_for_review = list(done_topics)
                if available_for_review:
                    review_keys.update(random.sample(available_for_review, min(4, len(available_for_review))))

            for dow in range(7):
                current_day = week_start + timedelta(days=dow)
                if current_day >= plan.end_date:
                    break

                day_plan = self._build_day_plan(
                    sorted_subjects, current_day, done_topics, week_topic_keys, review_keys
                )
                weekly.days[WEEKDAYS[dow]] = day_plan
                for s in day_plan.sessions:
                    key = f"{s.subject}:{s.topic}"
                    done_topics.add(key)
                    week_topic_keys.discard(key)
                    review_keys.discard(key)

            plan.weekly_plans.append(weekly)

        return plan

    def _build_day_plan(
        self, subjects: list[Subject], day: date, done_topics: set,
        new_keys: set, review_keys: set
    ) -> DayPlan:
        sessions = []
        available_minutes = int(self.daily_target_hours * 60)
        allocated = 0
        time_cursor = time(9, 0)

        for subject in subjects:
            eligible = []
            for t in subject.syllabus:
                key = f"{subject.name}:{t.name}"
                if t.is_completed:
                    continue
                if key in new_keys or key in review_keys:
                    eligible.append(t)
            if not eligible:
                continue

            for topic in eligible:
                if allocated >= available_minutes:
                    break

                slot = self._pick_slot(topic.difficulty, available_minutes - allocated)
                if slot <= 0:
                    continue

                total_minutes = time_cursor.hour * 60 + time_cursor.minute + slot
                if total_minutes >= 22 * 60:
                    break

                end_hour = total_minutes // 60
                end_min = total_minutes % 60
                end_time = time(end_hour, end_min)
                sessions.append(StudySession(
                    subject=subject.name,
                    topic=topic.name,
                    start_time=time_cursor,
                    end_time=end_time,
                    duration_minutes=slot,
                ))
                allocated += slot
                done_topics.add(f"{subject.name}:{topic.name}")

                h = time_cursor.hour + slot // 60
                m = time_cursor.minute + slot % 60 + 15
                time_cursor = time(min(h + m // 60, 22), m % 60)

            if allocated >= available_minutes:
                break

        return DayPlan(date=day, sessions=sessions)

    @staticmethod
    def _pick_slot(difficulty: Difficulty, remaining: int) -> int:
        mapping = {Difficulty.HARD: 60, Difficulty.MEDIUM: 45, Difficulty.EASY: 30}
        slot = mapping.get(difficulty, 45)
        return min(slot, remaining)
