from langchain_groq import ChatGroq
from .config import settings

# Initialize a Groq LLM client using LangChain's ChatGroq wrapper.
# Pulls the API key from the application settings.
llm = ChatGroq(
    api_key=settings.groq_api_key,
    # Model selection for generating responses.
    model_name="llama-3.3-70b-versatile",
    # Slight randomness for more natural responses while staying controlled.
    temperature=0.4,
    # Let the model decide the required token length (no hard limit specified).
    max_tokens=None,
)
