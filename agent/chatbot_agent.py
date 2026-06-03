import re
from datetime import date
from agent import StudyPlannerAgent


class ChatbotAgent:
    def __init__(self, planner: StudyPlannerAgent):
        self.planner = planner
        self.context = {}

    def process_message(self, message: str) -> str:
        msg = message.lower().strip()

        log_match = re.search(r'log session\s+(\w+)\s+(.+?)\s+(\d+)', message)
        if log_match:
            return self._log_session(log_match.group(1), log_match.group(2).strip(), int(log_match.group(3)))

        if re.search(r'\b(hi|hello|hey|hai)\b', msg):
            return self._greet()
        elif re.search(r'\b(analyze|analysis|syllabus|subjects?)\b', msg):
            return self._analyze()
        elif re.search(r'\b(plan|schedule|generate|create)\b', msg):
            return self._generate_plan()
        elif re.search(r'\b(tip|advice|suggest|recommend)\b', msg):
            return self._advice()
        elif re.search(r'\b(today|what.*(study|do))\b', msg):
            return self._todays_plan()
        elif re.search(r'\b(log|session|studied|done)\b', msg):
            return self._ask_log_details(message)
        elif re.search(r'\b(progress|summary|streak|status)\b', msg):
            return self._progress()
        elif re.search(r'\b(weak|hard|struggl|difficult|tough)\b', msg):
            return self._weak_subjects()
        elif re.search(r'\b(export)\b', msg):
            return self._export()
        elif re.search(r'\b(help|what can|commands)\b', msg):
            return self._help()
        elif re.search(r'\b(thank|thanks|thx)\b', msg):
            return "You're welcome! Keep up the great work with your studies! 📚"
        else:
            return self._fallback()

    def _greet(self):
        return (
            "👋 Hello! I'm your **Personalized Study Planner AI Assistant**!\n\n"
            "Here's what I can help you with:\n"
            "• 📊 **Analyze** your syllabus and identify weak subjects\n"
            "• 📅 **Generate** a personalized study plan\n"
            "• 📝 **Log** your study sessions\n"
            "• 📈 **Track** your progress and streaks\n"
            "• 💡 **Suggest** what to study today\n"
            "• 📤 **Export** your study plan\n\n"
            "Try saying: \"analyze my syllabus\" or \"generate a plan\"!"
        )

    def _analyze(self):
        try:
            analysis = self.planner.analyze()
            lines = ["**📊 Syllabus Analysis**\n"]
            lines.append(f"⏱ Total pending study hours: **{analysis['total_pending_hours']:.1f}h**")
            lines.append(f"⚠️ Weak subjects: **{', '.join(analysis['weak_subjects']) or 'None'}**")
            lines.append(f"📚 Hard topics remaining: **{len(analysis['hard_topics'])}**\n")
            lines.append("**Priority Scores:**")
            for subj, score in sorted(analysis['priorities'].items(), key=lambda x: -x[1]):
                bar = "🟪" * max(1, int(score * 5))
                lines.append(f"  {subj}: {bar} ({score:.2f})")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error analyzing syllabus: {str(e)}"

    def _generate_plan(self):
        try:
            plan = self.planner.generate_plan(weeks=4)
            lines = ["**📅 Study Plan Generated!**\n"]
            lines.append(f"📆 {plan.start_date} → {plan.end_date}")
            lines.append(f"🎯 Daily target: **{plan.daily_target_hours}h**\n")
            for i, week in enumerate(plan.weekly_plans, 1):
                hours = week.total_study_hours
                lines.append(f"**Week {i}** (starting {week.week_start}): {hours:.1f}h total")
                for day_name, day in week.days.items():
                    if day.sessions:
                        lines.append(f"  • {day_name}: {day.total_study_minutes}min")
                        for s in day.sessions[:2]:
                            lines.append(f"    └ {s.start_time}-{s.end_time}  {s.subject}: {s.topic}")
                        if len(day.sessions) > 2:
                            lines.append(f"    └ ... +{len(day.sessions)-2} more sessions")
            lines.append("\n✅ Plan also exported to data/study_plan.json")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error generating plan: {str(e)}"

    def _ask_log_details(self, message: str):
        m = re.search(r'log session\s+(\w+)\s+(.+?)\s+(\d+)', message)
        if m:
            return self._log_session(m.group(1), m.group(2).strip(), int(m.group(3)))
        return (
            "To log a study session, use:\n"
            "`log session <subject> <topic> <minutes>`\n\n"
            "Example: `log session Mathematics Linear Algebra 60`"
        )

    def _log_session(self, subject: str, topic: str, minutes: int):
        try:
            self.planner.log_study_session(subject, topic, minutes)
            return f"✅ Logged: **{subject}** - {topic} for **{minutes}min**!\n\nKeep up the great work! 🎉"
        except Exception as e:
            return f"❌ Error logging session: {str(e)}"

    def _progress(self):
        try:
            summary = self.planner.get_progress_summary()
            lines = ["**📈 Progress Summary**\n"]
            lines.append(f"🔥 Study streak: **{summary['streak']} days**")
            lines.append(f"📆 Days active this week: **{summary['days_active']}**")
            lines.append(f"⏱ Total minutes this week: **{summary['total_minutes']}**")
            lines.append(f"⚠️ Weak subjects: **{', '.join(summary['weak_subjects']) or 'None'}**")
            if summary.get('per_subject'):
                lines.append("\n**Per Subject:**")
                for subj, mins in summary['per_subject'].items():
                    bar = "📘" * max(1, mins // 15)
                    lines.append(f"  {subj}: {bar} ({mins}min)")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error fetching progress: {str(e)}"

    def _weak_subjects(self):
        try:
            analysis = self.planner.analyze()
            if analysis['weak_subjects']:
                lines = ["**⚠️ Weak Subjects Identified**\n"]
                for ws in analysis['weak_subjects']:
                    subj = next((s for s in self.planner.subjects if s.name == ws), None)
                    if subj:
                        lines.append(f"📕 **{ws}** - Confidence: **{subj.confidence_score:.0%}**")
                        hard = [t for t in subj.syllabus if t.difficulty.value == "hard" and not t.is_completed]
                        if hard:
                            lines.append(f"  Hard topics: {', '.join(t.name for t in hard)}")
                        lines.append(f"  Exam in: **{subj.days_until_exam} days**")
                        lines.append(f"  Suggested hours: **{subj.total_hours:.1f}h**")
                lines.append("\n💡 **Tip:** Focus on these subjects first! Increase daily study time for weak areas.")
                return "\n".join(lines)
            else:
                return "✅ Great job! You have no weak subjects at the moment. Keep maintaining your progress!"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _advice(self):
        try:
            analysis = self.planner.analyze()
            lines = ["**💡 Study Advice**\n"]
            if analysis['weak_subjects']:
                lines.append("📌 **Priority:** Focus on weak subjects first:")
                for ws in analysis['weak_subjects']:
                    subj = next((s for s in self.planner.subjects if s.name == ws), None)
                    if subj:
                        lines.append(f"  • **{ws}** - only {subj.days_until_exam} days until exam!")
                lines.append("")
            lines.append("📌 **Recommended study pattern:**")
            lines.append("  • 60min sessions for hard topics")
            lines.append("  • 45min for medium topics")
            lines.append("  • 30min for easy topics")
            lines.append("  • Take 15min breaks between sessions")
            lines.append("")
            lines.append("📌 **Tips:**")
            lines.append("  • Study your hardest subject when you're most alert (morning ☀️)")
            lines.append("  • Review weak topics before bed for better retention 🧠")
            lines.append("  • Mix difficult and easy topics to avoid burnout 🔄")
            lines.append("  • Stay consistent - even 30min daily helps! 📆")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _todays_plan(self):
        try:
            if not self.planner.current_plan:
                return "No study plan generated yet. Try saying **'generate a plan'** first!"
            today_name = date.today().strftime("%a")[:3]
            lines = [f"**📋 Today's Study Plan ({date.today()})**\n"]
            found = False
            for week in self.planner.current_plan.weekly_plans:
                for day_name, day in week.days.items():
                    if day_name.lower().startswith(today_name.lower()[:3]):
                        if day.sessions:
                            found = True
                            lines.append(f"⏱ Total: **{day.total_study_minutes}min**\n")
                            for s in day.sessions:
                                lines.append(f"  • **{s.subject}** - {s.topic}")
                                lines.append(f"    ⏰ {s.start_time} - {s.end_time} ({s.duration_minutes}min)")
                        else:
                            return "🎉 No study sessions scheduled for today! Enjoy your break!"
            if not found:
                return "No plan for today. Generate a plan with **'generate a plan'**"
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _export(self):
        try:
            if not self.planner.current_plan:
                self.planner.generate_plan(weeks=4)
            from pathlib import Path
            path = str(Path(__file__).parent.parent / "data" / "study_plan.json")
            self.planner.export_plan(path)
            return f"✅ Study plan exported to **{path}**"
        except Exception as e:
            return f"❌ Error exporting plan: {str(e)}"

    def _help(self):
        return (
            "**🤖 Available Commands**\n\n"
            "• `analyze` / `syllabus` - Analyze your syllabus\n"
            "• `generate plan` / `schedule` - Create a study plan\n"
            "• `log session <subject> <topic> <min>` - Log study session\n"
            "• `progress` / `summary` - View your progress\n"
            "• `weak subjects` - See weak areas\n"
            "• `advice` / `tips` - Get study recommendations\n"
            "• `today` - View today's plan\n"
            "• `export` - Export plan to JSON\n"
            "• `hello` / `hi` - Greeting\n"
            "• `help` - Show this help"
        )

    def _fallback(self):
        return (
            "🤔 I'm not sure I understood that. Here are some things you can ask:\n\n"
            "• \"analyze my syllabus\"\n"
            "• \"generate a study plan\"\n"
            "• \"log session Mathematics Calculus 60\"\n"
            "• \"show my progress\"\n"
            "• \"give me study advice\"\n"
            "• \"what should I study today?\"\n\n"
            "Type **`help`** to see all available commands!"
        )
