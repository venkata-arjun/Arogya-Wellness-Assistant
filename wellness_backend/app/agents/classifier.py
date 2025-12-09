from app.memory import get_llm


def is_wellness_query(message: str) -> bool:
    """
    Uses LLM reasoning (not keyword matching) to classify intent.
    Returns True if message is about symptoms, lifestyle, diet, exercise,
    health discomfort, or wellness advice.
    """

    llm = get_llm()

    prompt = f"""
You are an intent classifier. Do NOT answer the user's question.

Your task: decide ONLY whether the message is a *wellness-related query*.

A message **is wellness-related** if:
- It mentions symptoms (pain, headache, stomach issue, stress, fatigue, breathing, fever, etc.)
- It asks for diet advice
- It asks for exercise recommendations
- It asks for sleep or lifestyle help
- It expresses physical or mental wellness discomfort

A message is **NOT wellness-related** if it is about:
Technology, coding, assignments, jokes, movies, random chat, greetings, finance, weather, politics, etc.

Message: "{message}"

Answer STRICTLY with:
YES — if it is wellness-related  
NO — if it is NOT wellness-related
"""

    result = llm.invoke(prompt).content.strip().upper()

    return result.startswith("YES")
