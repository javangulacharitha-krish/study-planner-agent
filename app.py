#!/usr/bin/env python3
"""Flask Web Application for Personalized Study Planner."""

from pathlib import Path
from datetime import date
from flask import Flask, render_template, request, jsonify, session
from agent import StudyPlannerAgent
from agent.chatbot_agent import ChatbotAgent

app = Flask(__name__)
app.secret_key = "study-planner-secret-key-change-in-production"

BASE_DIR = Path(__file__).parent
SAMPLE_DATA = BASE_DIR / "data" / "sample_data.json"

planner = StudyPlannerAgent(daily_target_hours=4.0)
planner.load_data(str(SAMPLE_DATA))
chatbot = ChatbotAgent(planner)


def get_dashboard_data():
    analysis = planner.analyze()
    subjects_data = []
    for s in planner.subjects:
        subjects_data.append({
            "name": s.name,
            "confidence": round(s.confidence_score * 100),
            "total_hours": s.total_hours,
            "days_until_exam": s.days_until_exam,
            "is_weak": s.is_weak,
            "topics": [
                {"name": t.name, "difficulty": t.difficulty.value, "completed": t.is_completed}
                for t in s.syllabus
            ],
        })
    plan_data = None
    if planner.current_plan:
        plan_data = {
            "start": str(planner.current_plan.start_date),
            "end": str(planner.current_plan.end_date),
            "daily_target": planner.current_plan.daily_target_hours,
            "weeks": [
                {
                    "week_start": str(wp.week_start),
                    "days": {
                        dn: {
                            "date": str(dp.date),
                            "total_minutes": dp.total_study_minutes,
                            "sessions": [
                                {"subject": s.subject, "topic": s.topic, "start": str(s.start_time),
                                 "end": str(s.end_time), "duration": s.duration_minutes}
                                for s in dp.sessions
                            ],
                        }
                        for dn, dp in wp.days.items()
                    },
                }
                for wp in planner.current_plan.weekly_plans
            ],
        }
    progress = planner.get_progress_summary()
    serializable_analysis = {
        "priorities": analysis["priorities"],
        "weak_subjects": analysis["weak_subjects"],
        "hard_topics": analysis["hard_topics"],
        "total_pending_hours": analysis["total_pending_hours"],
    }
    return {
        "analysis": serializable_analysis,
        "subjects": subjects_data,
        "plan": plan_data,
        "progress": progress,
        "has_plan": planner.current_plan is not None,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    data = get_dashboard_data()
    return render_template("dashboard.html", **data)


@app.route("/api/analyze")
def api_analyze():
    data = get_dashboard_data()
    return jsonify(data)


@app.route("/api/plan/generate", methods=["POST"])
def api_generate_plan():
    weeks = request.json.get("weeks", 4) if request.is_json else 4
    planner.generate_plan(weeks=weeks)
    return jsonify({"success": True, "message": f"{weeks}-week study plan generated"})


@app.route("/api/plan", methods=["GET"])
def api_get_plan():
    data = get_dashboard_data()
    return jsonify({"plan": data["plan"], "has_plan": data["has_plan"]})


@app.route("/api/log", methods=["POST"])
def api_log_session():
    data = request.json
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    minutes = int(data.get("minutes", 30))
    if not subject or not topic:
        return jsonify({"success": False, "message": "Subject and topic are required"}), 400
    planner.log_study_session(subject, topic, minutes)
    return jsonify({"success": True, "message": f"Logged {minutes}min studying {subject} - {topic}"})


@app.route("/api/progress")
def api_progress():
    return jsonify(planner.get_progress_summary())


@app.route("/api/subjects")
def api_subjects():
    return jsonify(get_dashboard_data()["subjects"])


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"response": "Please say something!"})
    response = chatbot.process_message(message)
    return jsonify({"response": response})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    planner.__init__(daily_target_hours=4.0)
    planner.load_data(str(SAMPLE_DATA))
    return jsonify({"success": True, "message": "Data reset to initial state"})


if __name__ == "__main__":
    print("=" * 60)
    print("  Personalized Study Planner - Web Interface")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
