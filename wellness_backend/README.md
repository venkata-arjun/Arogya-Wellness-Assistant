# Arogya Wellness Assistant - Backend

A sophisticated multi-agent AI backend system that provides comprehensive wellness guidance using LangChain, Groq LLM, and a modular agent architecture. The system intelligently classifies health concerns, maintains conversation context via SQL and LangChain memory, and delivers personalized advice across diet, lifestyle, fitness, and symptom analysis.

## 🎯 Features

- **Multi-Agent Architecture**:
  - SymptomAgent: Analyzes and classifies health symptoms
  - DietAgent: Provides nutritional and dietary recommendations
  - FitnessAgent: Suggests physical activities and exercises
  - LifestyleAgent: Offers lifestyle and stress management advice
- **Intelligent Follow-Up Detection**:
  - Uses LLM to distinguish follow-ups from new queries
  - SQL database for conversation persistence
  - Context-aware responses that build on previous advice
- **Smart Section Classification**:
  - Automatically determines which advice section to update
  - Multi-level fallback with keyword matching
  - Handles user constraints and preferences
- **Dual Memory System**:
  - LangChain memory for in-session context
  - MySQL database for persistent history
  - Token-limited memory with automatic trimming
- **Non-Wellness Query Handling**:
  - Politely redirects off-topic questions
  - Maintains conversation focus on wellness
- **CORS Enabled**: Support for multi-origin requests

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL server running
- Groq API key (free from [console.groq.com](https://console.groq.com))

### Installation

1. **Clone and navigate**

```bash
cd wellness_backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
   Create `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=wellness_db
```

5. **Set up MySQL Database**

```sql
CREATE DATABASE wellness_db;
USE wellness_db;

CREATE TABLE wellness_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    is_follow_up BOOLEAN DEFAULT FALSE,
    target_section VARCHAR(50),
    final_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (user_id),
    INDEX (created_at)
);
```

6. **Run the server**

```bash
python -m uvicorn main:app --reload --port 8000
```

Server will start at `http://localhost:8000`

## 📁 Project Structure

```
wellness_backend/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base agent class
│   │   ├── symptom_agent.py        # Symptom analysis
│   │   ├── diet_agent.py           # Diet recommendations
│   │   ├── fitness_agent.py        # Fitness suggestions
│   │   ├── lifestyle_agent.py      # Lifestyle advice
│   │   ├── classifier.py           # Query classification
│   │   └── orchestrator.py         # Main orchestration logic
│   ├── config.py                   # Configuration settings
│   ├── db.py                       # Database operations
│   ├── llm.py                      # LLM & memory setup
│   ├── memory.py                   # LangChain memory management
│   └── schemas.py                  # Pydantic request/response models
├── main.py                         # FastAPI application entry
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
└── README.md
```

## 🔧 Key Technologies

- **FastAPI 0.110.0**: Modern async web framework
- **Uvicorn 0.29.0**: ASGI server
- **LangChain 0.1.20**: LLM orchestration framework
- **Groq LLama 3.3 70B**: High-speed language model
- **MySQL Connector**: Database operations
- **Pydantic 2.6.4**: Data validation

## 📡 API Endpoints

### POST `/api/wellness`

Process a wellness-related user message through the multi-agent system.

**Request:**

```json
{
  "user_id": "user_abc123",
  "message": "I have been having stomach discomfort for 2 days"
}
```

**Response:**

```json
{
  "user_id": "user_abc123",
  "final_output": {
    "symptom": "Stomach discomfort for 2 days",
    "observations": [
      "Symptom has been ongoing for 2 days",
      "May be related to diet or stress",
      ...
    ],
    "diet_guidance": [
      "Eat bland foods like crackers and rice",
      "Avoid spicy and fatty foods",
      ...
    ],
    "lifestyle_advice": [
      "Stay hydrated with plenty of water",
      "Practice stress-reducing techniques",
      ...
    ],
    "physical_activity_suggestions": [
      "Gentle walking to stimulate digestion",
      "Light yoga poses",
      ...
    ],
    "conclusion": "To manage your stomach discomfort..."
  }
}
```

### GET `/api/history/{user_id}`

Retrieve conversation history for a specific user.

**Response:**

```json
{
  "user_id": "user_abc123",
  "messages": [
    {
      "timestamp": "2025-12-09T10:30:00",
      "role": "user",
      "content": "I have stomach discomfort"
    },
    {
      "timestamp": "2025-12-09T10:30:05",
      "role": "SymptomAgent",
      "content": "Stomach discomfort for 2 days"
    },
    ...
  ]
}
```

## 🤖 Agent Architecture

### SymptomAgent

- **Purpose**: Analyze and classify user-reported symptoms
- **Input**: User message and conversation context
- **Output**: Structured symptom summary with observations
- **Next**: Routes to DietAgent or LifestyleAgent

### DietAgent

- **Purpose**: Provide personalized dietary recommendations
- **Input**: Symptom details and user context
- **Output**: 5+ diet guidance points specific to the symptom
- **Next**: Routes to FitnessAgent

### FitnessAgent

- **Purpose**: Suggest appropriate physical activities
- **Input**: Symptom details and fitness context
- **Output**: 5+ exercise suggestions
- **Next**: Routes to LifestyleAgent

### LifestyleAgent

- **Purpose**: Recommend lifestyle and stress management strategies
- **Input**: Symptom details and lifestyle context
- **Output**: 5+ lifestyle advice points
- **Next**: Routes to Orchestrator for final output

## 🔄 Processing Flow

### New Query Flow

```
1. User Message
   ↓
2. is_wellness_query() → Check if wellness-related
   ↓ (YES)
3. _is_follow_up_with_sql() → Check if follow-up
   ↓ (NEW QUERY)
4. Run all 4 agents in sequence:
   - SymptomAgent
   - DietAgent
   - FitnessAgent
   - LifestyleAgent
   ↓
5. _build_final_json_new() → Combine all outputs
   ↓
6. Save to SQL + LangChain Memory
   ↓
7. Return final_output to client
```

### Follow-Up Query Flow

```
1. User Message
   ↓
2. is_wellness_query() → Check if wellness-related
   ↓ (YES)
3. _is_follow_up_with_sql() → Check if follow-up
   ↓ (FOLLOW-UP)
4. _classify_followup_section() → Determine which section to update
   ↓
5. Run only relevant agent:
   - Diet section → DietAgent
   - Exercise section → FitnessAgent
   - Lifestyle section → LifestyleAgent
   - Observation section → SymptomAgent
   ↓
6. _build_final_json_followup() → Merge with previous output
   ↓
7. Save follow-up to SQL with target_section
   ↓
8. Return updated final_output to client
```

### Non-Wellness Query Flow

```
1. User Message
   ↓
2. is_wellness_query() → Check if wellness-related
   ↓ (NO)
3. _handle_non_wellness_query() → Polite redirection
   ↓
4. Return redirect message in JSON format
```

## 💾 Memory Management

### LangChain Memory

- **Type**: ConversationTokenBufferMemory
- **Limit**: 3000 tokens
- **Purpose**: In-session context and agent reference
- **Storage**: In-memory (Python process)
- **Format**: Tagged messages like `[SymptomAgent] ...`

### MySQL Database

- **Type**: Persistent relational storage
- **Purpose**: Long-term history and follow-up detection
- **Schema**: wellness_history table with:
  - user_id (indexed)
  - user_message
  - is_follow_up flag
  - target_section
  - final_json (structured advice)
  - created_at timestamp

## 🧠 Key Functions

### Core Orchestration

- `run_wellness_flow()` - Main entry point, routes all requests
- `_is_follow_up_with_sql()` - LLM-based follow-up detection using SQL data
- `_classify_followup_section()` - Determines which section to update
- `_handle_non_wellness_query()` - Handles off-topic questions

### JSON Building

- `_build_final_json_new()` - Combines all 4 agents' output
- `_build_final_json_followup()` - Merges updated section with previous

### Classification

- `is_wellness_query()` - Uses LLM to check wellness relevance
- `_classify_followup_section()` - 3-level fallback for section classification

### Utilities

- `_safe_json_loads()` - Robust JSON parsing with fallback
- `_add_memory_message()` - Stores tagged messages in LangChain memory

## 🔐 Security Features

- **LangChain Memory**: Token-limited to prevent context overflow
- **SQL Queries**: Parameterized to prevent injection
- **Environment Variables**: Sensitive data in `.env` (not in code)
- **CORS Configuration**: Configurable origin restrictions
- **Error Handling**: Graceful fallbacks without exposing system details

## 📊 Configuration

Edit `app/config.py` to customize:

- LLM model selection
- Memory token limits
- Database connection settings
- Agent behavior parameters

## 🐛 Debugging

### Enable Debug Logging

The system prints debug info:

```
[DEBUG] User: user_abc123
[DEBUG] Message: I have a headache
[DEBUG] Follow-up detected: False
[DEBUG] Target section for follow-up: diet_guidance
```

### Common Issues

**"No previous interaction found"**

- This is normal for first message
- System will process as new query

**"Invalid target section: None"**

- Section classification failed
- System falls back to new query processing

**"Follow-up detection error"**

- LLM call failed
- Check Groq API key and rate limits

**MySQL Connection Error**

- Verify `.env` credentials
- Ensure MySQL server is running
- Check database exists

## 🛠️ Development

### Run in Development Mode

```bash
python -m uvicorn main:app --reload --port 8000
```

### Run with Logging

```bash
python -m uvicorn main:app --reload --log-level debug
```

### Test Endpoints with cURL

```bash
# Test wellness query
curl -X POST "http://localhost:8000/api/wellness" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "I have a headache"}'

# Get history
curl "http://localhost:8000/api/history/test_user"

# API docs
curl "http://localhost:8000/docs"
```

## 📚 API Documentation

Interactive Swagger UI documentation available at:

```
http://localhost:8000/docs
```

ReDoc documentation available at:

```
http://localhost:8000/redoc
```

## 🔄 Response Structure

All wellness responses follow this schema:

```json
{
  "symptom": "string (primary health concern)",
  "observations": ["string (5+ observation points)"],
  "diet_guidance": ["string (5+ diet recommendations)"],
  "lifestyle_advice": ["string (5+ lifestyle tips)"],
  "physical_activity_suggestions": ["string (5+ exercise recommendations)"],
  "conclusion": "string (synthesized summary and action plan)"
}
```

## 🌐 Environment Variables

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key

# MySQL Database
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=wellness_db

# Optional: FastAPI Settings
ENVIRONMENT=development
DEBUG=true
```

## 📦 Dependencies

Core dependencies:

- **FastAPI**: Web framework
- **LangChain**: LLM orchestration
- **Groq**: Fast LLM inference
- **Pydantic**: Data validation
- **python-dotenv**: Environment management
- **MySQL Connector**: Database driver

See `requirements.txt` for full list with versions.

## 🚀 Deployment

### Production Checklist

- [ ] Set strong `.env` credentials
- [ ] Use HTTPS for API calls
- [ ] Restrict CORS to specific origins
- [ ] Configure proper logging
- [ ] Set up database backups
- [ ] Use environment-specific config
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerting

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Performance Optimization

- **Token Limiting**: 3000-token memory prevents slowdown
- **Agent Routing**: Only relevant agents run for follow-ups
- **Caching**: Consider Redis for frequent queries
- **Async Processing**: FastAPI handles concurrent requests
- **Database Indexing**: Indexed on user_id and timestamp

## 🤝 Contributing

When adding new agents:

1. Inherit from `BaseAgent` in `base.py`
2. Implement `run(state)` method
3. Return `{"state": updated_state, "next": next_agent_name}`
4. Update orchestrator routing
5. Add tests

## 📄 License

Part of the Arogya Wellness Assistant project.

## 🆘 Support

For issues:

1. Check debug logs
2. Verify `.env` configuration
3. Ensure database connectivity
4. Check Groq API quota
5. Review error messages in response

Contact project maintainers for technical support.
