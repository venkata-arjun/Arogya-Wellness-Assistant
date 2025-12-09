class DietAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        user_msg = state.get("user_input", "")
        symptom = state.get("symptom_summary", "")

        prompt = f"""
You are a diet specialist. Give 5 short, clear diet guidance points 
for the user's symptom.

Symptom: {symptom}
User message: {user_msg}

Each point must be a short standalone sentence (no numbering).
Return points separated by semicolons.
"""

        try:
            resp = self.llm.invoke(prompt).content
        except:
            resp = "Stay hydrated; Eat light meals; Avoid heavy foods; Include soothing foods; Reduce irritants."

        tips = [x.strip() for x in resp.split(";") if x.strip()]
        state["diet_tip"] = tips

        return {"state": state, "next": "LifestyleAgent"}
