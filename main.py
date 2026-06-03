#!/usr/bin/env python3
"""Personalized Study Planner AI Agent - CLI Entry Point."""

import sys
from pathlib import Path
from agent import StudyPlannerAgent

SAMPLE_DATA = Path(__file__).parent / "data" / "sample_data.json"


def print_banner():
    print("=" * 60)
    print("  Personalized Study Planner AI Agent")
    print("=" * 60)


def print_analysis(agent: StudyPlannerAgent):
    analysis = agent.analyze()
    print(f"\n-- Syllabus Analysis --")
    print(f"{'-' * 40}")
    print(f"  Total pending study hours: {analysis['total_pending_hours']:.1f}h")
    print(f"  Weak subjects: {', '.join(analysis['weak_subjects']) or 'None'}")
    print(f"  Hard topics remaining: {len(analysis['hard_topics'])}")
    print(f"\n  Priority scores:")
    for subj, score in sorted(analysis['priorities'].items(), key=lambda x: -x[1]):
        bar = "#" * int(score * 20)
        print(f"    {subj:20s} {bar} {score:.2f}")


def print_plan(agent: StudyPlannerAgent):
    if not agent.current_plan:
        print("\nNo plan generated.")
        return
    print(f"\n>> Study Plan ({agent.current_plan.start_date} -> {agent.current_plan.end_date})")
    print(f"{'-' * 60}")
    for i, week in enumerate(agent.current_plan.weekly_plans, 1):
        print(f"\n  Week {i} (starting {week.week_start}): {week.total_study_hours:.1f}h total")
        for day_name, day in week.days.items():
            if day.sessions:
                print(f"    {day_name}: {day.total_study_minutes}min")
                for s in day.sessions[:2]:
                    print(f"      + {s.start_time}-{s.end_time}  {s.subject}: {s.topic}")
                if len(day.sessions) > 2:
                    print(f"      + ... +{len(day.sessions)-2} more sessions")


def print_progress(agent: StudyPlannerAgent):
    summary = agent.get_progress_summary()
    print(f"\n-- Progress Summary --")
    print(f"{'-' * 40}")
    print(f"  Study streak: {summary['streak']} days")
    print(f"  Days active this week: {summary['days_active']}")
    print(f"  Total minutes this week: {summary['total_minutes']}")
    if summary["per_subject"]:
        print(f"  Per subject:")
        for subj, mins in summary["per_subject"].items():
            print(f"    {subj}: {mins}min")


def interactive_menu():
    agent = StudyPlannerAgent(daily_target_hours=4.0)
    agent.load_data(str(SAMPLE_DATA))

    while True:
        print_banner()
        print("\n  [1] Analyze syllabus")
        print("  [2] Generate 4-week study plan")
        print("  [3] Log today's study session")
        print("  [4] View progress summary")
        print("  [5] Export plan to JSON")
        print("  [q] Quit")
        choice = input("\n  Select an option: ").strip().lower()

        if choice == "1" or choice == "analyze":
            print_analysis(agent)

        elif choice == "2" or choice == "plan":
            agent.generate_plan(weeks=4)
            print_plan(agent)
            agent.export_plan(str(Path(__file__).parent / "data" / "study_plan.json"))
            print("\n  + Plan exported to data/study_plan.json")

        elif choice == "3" or choice == "log":
            subj = input("  Subject name: ").strip()
            topic = input("  Topic studied: ").strip()
            mins = input("  Minutes studied: ").strip()
            agent.log_study_session(subj, topic, int(mins) if mins.isdigit() else 30)
            print(f"  + Logged: {subj} - {topic} ({mins or 30}min)")

        elif choice == "4" or choice == "progress":
            print_progress(agent)

        elif choice == "5" or choice == "export":
            agent.generate_plan(weeks=4)
            agent.export_plan(str(Path(__file__).parent / "data" / "study_plan.json"))
            print("  + Exported to data/study_plan.json")

        elif choice == "q" or choice == "quit":
            print("\n  Good luck with your studies!\n")
            break

        else:
            print("  Invalid option. Try again.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--web":
            from app import app
            print("=" * 60)
            print("  Personalized Study Planner - Web Interface")
            print("  http://127.0.0.1:5000")
            print("=" * 60)
            app.run(debug=True, host="0.0.0.0", port=5000)
            sys.exit(0)
        elif sys.argv[1] == "--quick":
            agent = StudyPlannerAgent()
            agent.load_data(str(SAMPLE_DATA))
            print_analysis(agent)
            agent.generate_plan(weeks=4)
            print_plan(agent)
            agent.export_plan(str(Path(__file__).parent / "data" / "study_plan.json"))
            print(f"\n  + Plan exported to data/study_plan.json")
            sys.exit(0)
    interactive_menu()
