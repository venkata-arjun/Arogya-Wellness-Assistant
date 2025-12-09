class LifestyleAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, state):
        user_msg = state.get("user_input", "")
        symptom = state.get("symptom_summary", "")

        prompt = f"""
You are a lifestyle advisor. Give 5 short lifestyle improvement points 
related to the user's symptom.

Symptom: {symptom}
User message: {user_msg}

Return short, direct points separated by semicolons.
No numbering.
"""

        try:
            resp = self.llm.invoke(prompt).content
        except:
            resp = "Rest properly; Reduce stress; Limit screens; Maintain a calm routine; Keep environment quiet."

        tips = [x.strip() for x in resp.split(";") if x.strip()]
        state["lifestyle_tip"] = tips

        return {"state": state, "next": "FitnessAgent"}
