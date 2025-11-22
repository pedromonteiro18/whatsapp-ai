# Deep-Agent Hospitality Concierge (PoC)

A proof-of-concept implementation of a LangChain deep-agent powered AI concierge for the WhatsApp hospitality platform. This module runs in parallel with the existing message processor to enable safe testing and comparison.

## Overview

This implementation replaces deterministic regex-based intent detection with an intelligent deep-agent system that:

- **Understands intent naturally** - No more regex patterns, AI comprehends what guests want
- **Uses specialized subagents** - Delegates complex tasks to focused experts
- **Maintains persistent memory** - Learns and remembers guest preferences across sessions
- **Plans multi-step workflows** - Breaks down complex requests autonomously
- **Provides tool-based actions** - Structured interactions with booking system

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Main Concierge Agent                       │
│  (Router/Coordinator with TodoList & Filesystem Middleware) │
└───────────────┬─────────────┬───────────────┬───────────────┘
                │             │               │
        ┌───────▼──────┐ ┌───▼────────┐ ┌────▼────────────┐
        │   Booking    │ │  Activity  │ │   Knowledge     │
        │  Specialist  │ │   Guide    │ │   Assistant     │
        └──────────────┘ └────────────┘ └─────────────────┘
                │             │               │
        ┌───────▼─────────────▼───────────────▼────────────┐
        │           LangChain Tools Layer                    │
        │  (search_activities, create_booking, etc.)        │
        └───────────────────┬───────────────────────────────┘
                            │
        ┌───────────────────▼───────────────────────────────┐
        │      Django Services & Models                      │
        │  (BookingService, Activity, TimeSlot, etc.)       │
        └───────────────────────────────────────────────────┘
```

## Components

### 1. **Tools** (`tools.py`)
LangChain tools wrapping Django services:

**Activity Tools:**
- `search_activities` - Find activities by category, price, duration
- `get_activity_details` - Get comprehensive activity information
- `check_time_slots` - Show available booking times

**Booking Tools:**
- `create_pending_booking` - Create reservation (requires confirmation)
- `get_user_bookings` - View user's bookings
- `cancel_booking` - Cancel a reservation

**Recommendation Tools:**
- `get_ai_recommendations` - Personalized activity suggestions

**Knowledge Tools:**
- `search_resort_knowledge` - Resort information and FAQs

### 2. **Specialized Subagents** (`subagents.py`)

**booking_specialist**
- Handles complete booking workflows
- Tools: All activity and booking tools
- Guides guest through: search → slots → confirmation

**activity_guide**
- Provides personalized recommendations
- Tools: Search, details, recommendations
- Learns preferences from conversation and history

**knowledge_assistant**
- Answers resort information questions
- Tools: Resort knowledge base search
- Covers policies, amenities, dining, etc.

### 3. **System Prompts** (`prompts.py`)
Defines personality and behavior for each agent:
- Main concierge: Warm, friendly coordinator
- Booking specialist: Efficient, detail-oriented
- Activity guide: Enthusiastic recommender
- Knowledge assistant: Accurate information provider

### 4. **Main Agent** (`agent.py`)
Core deep-agent setup with:
- InMemoryStore for persistent guest memory
- Composite backend (ephemeral `/workspace/`, persistent `/memories/`)
- TodoList, Filesystem, and SubAgent middleware
- Direct access to all tools

### 5. **Views & Tasks** (`views.py`, `tasks.py`)
- REST API endpoint for testing: `/api/deep-agent/test/`
- Parallel webhook: `/api/whatsapp/deep-agent/webhook/`
- Celery task for async processing
- Health check endpoint: `/api/deep-agent/health/`

## Installation

### 1. Install Dependencies

The deep-agent dependencies have already been added to `backend/requirements.txt`:

```bash
pip install -r backend/requirements.txt
```

This installs:
- `deepagents` - Deep-agent framework
- `langgraph` - Agent orchestration
- `langchain-core` - LangChain core
- `langchain-openai` - OpenAI/OpenRouter integration

### 2. Environment Variables

The deep-agent uses your existing configuration from `.env`:

```bash
# AI Configuration (already configured)
OPENROUTER_API_KEY=your_openrouter_key  # Or OPENAI_API_KEY
AI_MODEL=openai/gpt-4  # Or anthropic/claude-3-sonnet, etc.

# Booking Configuration (already configured)
BOOKING_WEB_APP_URL=http://localhost:5173
```

No additional configuration needed!

### 3. Run Database Migrations

```bash
python backend/manage.py migrate
```

### 4. Seed Test Data (Optional)

```bash
# Create sample activities
python backend/manage.py seed_activities

# Generate time slots
python backend/manage.py generate_timeslots --days 30

# Download activity images (requires PEXELS_API_KEY)
python backend/manage.py download_activity_images
```

## Usage

### Testing via API (Direct)

Test the deep-agent without WhatsApp integration:

```bash
curl -X POST http://localhost:8000/api/deep-agent/test/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+1234567890",
    "message": "Show me water activities"
  }'
```

Response:
```json
{
  "success": true,
  "response": "🌴 I'd be happy to show you our water activities! We have some amazing options...",
  "metadata": {
    "message_count": 2,
    "model_used": "openai/gpt-4",
    "thread_id": "guest-+1234567890"
  }
}
```

### Testing via Python

```python
from backend.deep_agent.agent import process_message

# Simple query
result = process_message("+1234567890", "What activities do you have?")
print(result["response"])

# Booking request (will use booking_specialist subagent)
result = process_message("+1234567890", "I want to book kayaking for tomorrow")
print(result["response"])

# Knowledge query (will use knowledge_assistant subagent)
result = process_message("+1234567890", "What time is check-in?")
print(result["response"])
```

### Testing via Celery Task

```python
from backend.deep_agent.tasks import process_deep_agent_message

# Queue message for async processing
task = process_deep_agent_message.delay(
    user_phone="+1234567890",
    message_content="I want to book scuba diving"
)

# Check task status
print(task.status)  # PENDING, SUCCESS, FAILURE
```

### Health Check

```bash
curl http://localhost:8000/api/deep-agent/health/
```

Response:
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "model": "openai/gpt-4",
  "tools_count": 8,
  "subagents_count": 3,
  "subagent_names": ["booking_specialist", "activity_guide", "knowledge_assistant"]
}
```

## Example Conversations

### 1. Activity Discovery

**User:** Show me activities

**Agent:** 🌴 I'd love to help you discover our amazing activities! We have five categories:

🏄 **Watersports** - Kayaking, snorkeling, scuba diving
💆 **Spa** - Massages, facials, wellness treatments
🍽️ **Dining** - Cooking classes, wine tastings
🏔️ **Adventure** - Hiking, rock climbing, zip-lining
🧘 **Wellness** - Yoga, meditation, fitness classes

What interests you most, or would you like personalized recommendations based on your preferences?

---

### 2. Booking Workflow (Uses booking_specialist subagent)

**User:** I want to book kayaking for tomorrow

**Agent:** *[Launches booking_specialist subagent]*

Great choice! I'd love to help you book kayaking. Let me ask a few quick questions:

- How many people will be participating?
- Do you prefer morning (8-11am), afternoon (12-3pm), or evening (4-6pm)?

**User:** 2 people, morning

**Agent:** Perfect! Here are the available morning kayaking slots for tomorrow:

1. Saturday, January 18 at 09:00 AM
   👥 8 spots available

2. Saturday, January 18 at 10:30 AM
   👥 10 spots available

Which time works best for you?

**User:** 9am

**Agent:** Excellent! Let me confirm the details:

✓ Activity: Kayaking Adventure
✓ Date & Time: Saturday, January 18 at 9:00 AM
✓ Participants: 2
✓ Total Price: $150.00

Should I create this booking for you?

**User:** Yes

**Agent:** ✅ Booking created successfully!

**Booking Details:**
Activity: Kayaking Adventure
Date & Time: Saturday, January 18 at 9:00 AM
Participants: 2
Total Price: $150.00 USD
Status: Pending Confirmation
Booking ID: abc12345

⏰ **Action Required:**
Please confirm your booking within 30 minutes:
http://localhost:5173/bookings/abc12345-...

Your spot is temporarily reserved until 10:45 AM.

---

### 3. Personalized Recommendations (Uses activity_guide subagent)

**User:** What should I do today? I like adventure

**Agent:** *[Launches activity_guide subagent]*

Based on your interest in adventure, here are my top recommendations:

🏔️ **Rock Climbing Experience**
Price: $95 | Duration: 3h | Difficulty: Intermediate
Why it's perfect for you: Great for adventure seekers! Our certified instructors will guide you through beginner and intermediate routes with stunning ocean views.

🌊 **Coastline Kayaking**
Price: $75 | Duration: 2h | Difficulty: Beginner
Why it's perfect for you: Combines adventure with nature exploration. Paddle through sea caves and spot marine life - perfect first-timer adventure!

🪂 **Zip-lining Canopy Tour**
Price: $110 | Duration: 2.5h | Difficulty: Moderate
Why it's perfect for you: Ultimate adrenaline rush! Soar through the forest canopy on 8 different zip lines. No experience needed!

Which of these sounds most appealing, or would you like me to look for something different?

---

### 4. Resort Knowledge (Uses knowledge_assistant subagent)

**User:** What time is check-in and do you have WiFi?

**Agent:** *[Launches knowledge_assistant subagent]*

**Resort Information:**

**Q: What are the check-in and check-out times?**
Check-in is at 3:00 PM and check-out is at 11:00 AM. Early check-in and late check-out may be available upon request, subject to availability.

**Q: Is WiFi available?**
Yes, complimentary high-speed WiFi is available throughout the resort, including guest rooms, lobby, pool areas, and restaurants.

Need anything else about the resort?

## Memory Management

The agent maintains persistent memory for each guest:

```
/memories/
  └── guests/
      └── +1234567890/
          ├── preferences.md      # Learned preferences
          ├── booking_history.md  # Past bookings summary
          └── conversations.md    # Conversation highlights
```

**Example preferences.md:**
```markdown
# Guest Preferences for +1234567890

## Interests
- Adventure activities (rock climbing, zip-lining)
- Morning time slots preferred
- Budget: $50-150 per activity

## Past Bookings
- Kayaking Adventure (loved it!)
- Scuba Diving (first time, enjoyed)

## Notes
- Traveling with partner
- Interested in trying new experiences
- Prefers outdoor activities over spa
```

Returning guests receive personalized greetings and recommendations based on this memory!

## Testing

### Run Unit Tests

```bash
# Test all deep-agent tools
python backend/manage.py test backend.deep_agent.tests

# Test specific tool
python backend/manage.py test backend.deep_agent.tests.test_tools.SearchActivitiesToolTest

# With verbosity
python backend/manage.py test backend.deep_agent.tests --verbosity=2
```

### Integration Testing

```bash
# Test simple query
curl -X POST http://localhost:8000/api/deep-agent/test/ \
  -H "Content-Type: application/json" \
  -d '{"user_phone": "+1234567890", "message": "Hello"}'

# Test booking flow
curl -X POST http://localhost:8000/api/deep-agent/test/ \
  -H "Content-Type: application/json" \
  -d '{"user_phone": "+1234567890", "message": "I want to book kayaking"}'

# Test knowledge query
curl -X POST http://localhost:8000/api/deep-agent/test/ \
  -H "Content-Type: application/json" \
  -d '{"user_phone": "+1234567890", "message": "What are your pool hours?"}'
```

## Comparison with Existing System

| Feature | Old System | Deep-Agent System |
|---------|-----------|------------------|
| **Intent Detection** | Regex patterns | Natural language understanding |
| **Conversation Flow** | Hardcoded state machine | AI-driven planning |
| **Context Management** | Redis key-value | Filesystem + persistent memory |
| **Task Delegation** | N/A | Specialized subagents |
| **Personalization** | Limited | Learns preferences over time |
| **Flexibility** | Rigid workflows | Adaptive conversations |
| **Error Handling** | Pattern matching fails | Graceful fallbacks |
| **Maintenance** | Add regex for each intent | Add tools/prompts |

### Performance Considerations

**Advantages:**
- More natural conversations
- Better intent understanding
- Persistent memory across sessions
- Self-planning for complex tasks
- Easier to extend (add tools vs regex)

**Trade-offs:**
- Higher API costs (more LLM calls)
- Slightly slower response time
- More complex debugging
- Requires LLM availability

### When to Use Each

**Use Old System:**
- High-volume, cost-sensitive scenarios
- Simple, predictable workflows
- When LLM availability is unreliable

**Use Deep-Agent:**
- Complex, multi-turn conversations
- Personalized guest experiences
- When flexibility is prioritized
- Research and experimentation

## Extending the System

### Add a New Tool

```python
# In tools.py
from langchain_core.tools import tool

@tool
def check_weather(
    location: str,
    date: str,
    runtime: Annotated[ToolRuntime, "Runtime injection"] = None,
) -> str:
    """Check weather forecast for a location and date."""
    # Implementation here
    return f"Weather for {location} on {date}: Sunny, 78°F"

# Add to ALL_TOOLS list
ALL_TOOLS = [
    # ... existing tools
    check_weather,
]
```

### Add a New Subagent

```python
# In subagents.py
def get_subagent_configs() -> List[dict]:
    return [
        # ... existing subagents
        {
            "name": "weather_specialist",
            "description": "Provides weather forecasts and outdoor activity planning",
            "system_prompt": WEATHER_SPECIALIST_PROMPT,
            "tools": [check_weather, search_activities],
        },
    ]
```

### Customize Prompts

Edit `prompts.py` to adjust agent personality and behavior:

```python
MAIN_CONCIERGE_PROMPT = """You are Maya, a friendly AI concierge...

[Customize personality, capabilities, guidelines, etc.]
"""
```

## Troubleshooting

### Agent Not Responding

```python
# Check agent health
from backend.deep_agent.agent import get_agent

agent = get_agent()
print(f"Agent initialized: {agent is not None}")
print(f"Model: {agent.model}")
```

### Tools Not Working

```python
# Test individual tool
from backend.deep_agent.tools import search_activities

result = search_activities.invoke({"category": "watersports"})
print(result)
```

### Memory Not Persisting

The PoC uses InMemoryStore which is lost on restart. For production:

```python
# In agent.py, replace InMemoryStore with PostgresStore
from langgraph.store.postgres import PostgresStore

self.store = PostgresStore(
    connection_string="postgresql://user:pass@localhost/db"
)
```

## Future Enhancements

1. **PostgreSQL Store** - Persistent memory across restarts
2. **Vector Knowledge Base** - Replace hardcoded FAQs with RAG
3. **Streaming Responses** - For long responses in real-time
4. **Multi-language Support** - Detect and respond in guest's language
5. **Human-in-the-Loop** - Escalation to human agents
6. **Analytics Dashboard** - Track agent performance metrics
7. **A/B Testing Framework** - Compare old vs new system empirically

## Contributing

When adding features:

1. **Add tests** - Every new tool needs unit tests
2. **Update prompts** - Document new capabilities in system prompts
3. **Extend docs** - Update this README with usage examples
4. **Test thoroughly** - Verify with real conversation flows

## License

Same as parent project.

## Support

For questions or issues:
- Check logs: `logs/whatsapp_chatbot.log`
- Review test cases: `tests/test_tools.py`
- Inspect agent state via health endpoint

---

**Status:** Proof of Concept ✨
**Version:** 0.1.0
**Last Updated:** 2025-01-17
