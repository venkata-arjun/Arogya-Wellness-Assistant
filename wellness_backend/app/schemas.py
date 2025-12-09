from pydantic import BaseModel
from typing import List


# Input schema for wellness-related requests from the client.
class WellnessRequest(BaseModel):
    user_id: str  # Unique identifier for the user
    message: str  # The user's query or wellness concern


# Represents a single message entry in the user's stored history.
class HistoryMessage(BaseModel):
    timestamp: str  # ISO-formatted timestamp of the message
    role: str  # 'user' or 'assistant'
    content: str  # The actual message text


# Response structure for returning a user's full conversation history.
class HistoryResponse(BaseModel):
    user_id: str  # User identifier
    messages: List[HistoryMessage]  # Chronological list of stored messages
