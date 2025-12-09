class SymptomAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        user_msg = state.get("user_input", "")

        prompt = f"""
You are a medical triage assistant. Summarize the user's health concern in ONE short line.

User message:
{user_msg}

Summary should be short, clear, and symptom-focused.
No solutions. No advice. Just a one-line issue summary.
"""

        try:
            summary = self.llm.invoke(prompt).content.strip()
        except:
            summary = "The user described a wellness issue."

        state["symptom_summary"] = summary

        return {"state": state, "next": "DietAgent"}
