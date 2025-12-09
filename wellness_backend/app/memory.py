from langchain.memory import ConversationTokenBufferMemory
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

# Load environment variables for API access.
load_dotenv()

# In-memory dictionary to store per-user conversation memory instances.
_user_memories = {}


def get_llm():
    # Create a fresh Groq LLM client with deterministic output.
    return ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0,
    )


def get_memory(user_id: str):
    # Create a new memory buffer for the user if it does not exist.
    if user_id not in _user_memories:
        _user_memories[user_id] = ConversationTokenBufferMemory(
            llm=get_llm(),  # LLM used for token counting and summarization
            max_token_limit=3000,  # Memory trims itself when token budget is exceeded
            return_messages=True,  # Ensures stored items are message objects, not plain text
        )
    # Return the existing or newly created memory instance.
    return _user_memories[user_id]
