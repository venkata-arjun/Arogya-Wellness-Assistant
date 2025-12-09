class FitnessAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        user_msg = state.get("user_input", "")
        symptom = state.get("symptom_summary", "")

        prompt = f"""
You are a fitness advisor. Give 5 short physical activity suggestions
based on the user's symptom.

Symptom: {symptom}
User message: {user_msg}

Keep points safe, simple, and beginner friendly.
Return points separated by semicolons. No numbering.
"""

        try:
            resp = self.llm.invoke(prompt).content
        except:
            resp = "Avoid heavy exercise; Do light stretching; Try slow walking; Focus on breathing; Stop if discomfort occurs."

        tips = [x.strip() for x in resp.split(";") if x.strip()]
        state["fitness_tip"] = tips

        return {"state": state, "next": None}  # last agent
