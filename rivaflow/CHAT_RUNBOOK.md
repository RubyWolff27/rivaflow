# RivaFlow Chat Feature - Runbook & Validation

## Architecture Overview

**Stack Detection:**
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS (port 5176)
- **Backend**: FastAPI + Python 3.11+ (port 8000)
- **Database**: SQLite (~/.rivaflow/rivaflow.db)
- **LLM Service**: Ollama with llama3.1:8b (port 11434)

**Chat Flow:**
1. User sends message in React Chat UI
2. Frontend calls POST /api/chat/ with conversation history
3. Backend proxies request to Ollama at http://localhost:11434/api/chat
4. Ollama returns response, backend forwards to frontend
5. Frontend displays assistant reply in chat UI

---

## Service Management

### Start All Services

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Start FastAPI backend
cd /Users/rubertwolff/scratch/rivaflow
uvicorn rivaflow.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Vite frontend
cd /Users/rubertwolff/scratch/web
npm run dev
```

### Stop Services

```bash
# Ollama: Ctrl+C in Terminal 1
# Backend: Ctrl+C in Terminal 2
# Frontend: Ctrl+C in Terminal 3
```

### Check Service Status

```bash
# Ollama
curl http://localhost:11434/api/tags

# Backend
curl http://localhost:8000/health

# Frontend
# Open browser to http://localhost:5176
```

---

## Testing & Validation

### 1. Verify Ollama Installation

```bash
# Check Ollama is installed
which ollama
# Expected: /opt/homebrew/bin/ollama

# Check llama3.1:8b model is available
ollama list
# Expected: llama3.1:8b should be listed

# Test Ollama directly
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [{"role": "user", "content": "Say hello"}],
  "stream": false
}'
# Expected: JSON response with assistant message
```

### 2. Test Backend Chat Endpoint

```bash
# Get auth token (login first via UI or create test user)
# Then test chat endpoint

curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is BJJ?"}
    ]
  }'

# Expected: {"reply": "Brazilian Jiu-Jitsu is..."}
```

### 3. Test Frontend Chat UI

1. Open http://localhost:5176/login
2. Login with test credentials
3. Navigate to http://localhost:5176/chat
4. Type a message: "Tell me about Brazilian Jiu-Jitsu"
5. Click Send
6. Verify:
   - Loading state shows "Thinking..."
   - Assistant reply appears
   - Conversation history is maintained
   - Can send follow-up messages

### 4. Test LLM Tool Stubs

```bash
# Test week report stub
curl -X GET "http://localhost:8000/api/llm-tools/report/week?week_start=2024-01-15" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected: {"summary": "Week starting...", "sessions": [...]}

# Test partners summary stub
curl -X GET "http://localhost:8000/api/llm-tools/partners/summary?start=2024-01-01&end=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected: {"partners": [...]}
```

---

## Validation Checklist

### Installation & Setup
- [ ] Ollama installed via homebrew
- [ ] llama3.1:8b model pulled
- [ ] httpx added to requirements.txt
- [ ] All services start without errors

### Backend
- [ ] /api/chat/ endpoint exists
- [ ] ChatRequest/ChatResponse models defined
- [ ] Proxies to Ollama correctly
- [ ] Returns 504 on timeout (60s)
- [ ] Returns 502 on Ollama service errors
- [ ] Requires authentication (JWT)
- [ ] CORS allows frontend origin

### Frontend
- [ ] Chat.tsx component created
- [ ] Route added to App.tsx at /chat
- [ ] Message list displays correctly
- [ ] User messages right-aligned (blue)
- [ ] Assistant messages left-aligned (gray)
- [ ] Loading state shows "Thinking..."
- [ ] Input disabled during loading
- [ ] Send button disabled when empty/loading
- [ ] Enter key sends message
- [ ] Conversation history maintained
- [ ] Error handling displays error messages

### LLM Tool Contracts
- [ ] GET /api/llm-tools/report/week endpoint exists
- [ ] Accepts week_start query parameter
- [ ] Returns {summary, sessions} structure
- [ ] GET /api/llm-tools/partners/summary endpoint exists
- [ ] Accepts start/end query parameters
- [ ] Returns {partners} structure
- [ ] PrivacyService.redact_for_llm() method exists
- [ ] All stubs documented as "TODO"

### End-to-End
- [ ] Can login and navigate to /chat
- [ ] Can send message and receive reply
- [ ] Conversation context maintained across messages
- [ ] No CORS errors in browser console
- [ ] No authentication errors
- [ ] Response time reasonable (<10s for simple queries)

---

## Future: Adding LLM Tools (Function Calling)

When you want the LLM to call RivaFlow functions:

### 1. Implement Tool Backend

Update stub endpoints in `api/routes/llm_tools.py`:
```python
@router.get("/report/week", response_model=WeekReportResponse)
async def get_week_report_for_llm(week_start: date, current_user: dict = Depends(get_current_user)):
    # Replace stub with actual implementation
    report_service = ReportService()
    sessions = report_service.get_sessions(current_user["id"], week_start, week_start + timedelta(days=7))

    # Redact sessions for LLM
    redacted = [PrivacyService.redact_for_llm(s) for s in sessions]

    # Generate natural language summary
    summary = f"Week of {week_start}: {len(sessions)} training sessions"

    return WeekReportResponse(summary=summary, sessions=redacted)
```

### 2. Define Tool Schema

Create tool definitions for Ollama (future feature - Ollama doesn't support tools yet):
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_week_report",
            "description": "Get training report for a specific week",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_start": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date of the week (YYYY-MM-DD)",
                    }
                },
                "required": ["week_start"],
            },
        },
    }
]
```

### 3. Update Chat Endpoint

Modify `api/routes/chat.py` to:
- Send tools array to Ollama (when supported)
- Detect function calls in response
- Execute functions locally
- Send results back to LLM
- Return final response to user

---

## Troubleshooting

### Ollama Not Responding

```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
killall ollama
ollama serve
```

### Chat Returns 504 Timeout

- LLM response taking >60s
- Increase timeout in `api/routes/chat.py`: `TIMEOUT = 120.0`
- Or switch to smaller model: `llama3.2:3b`

### Chat Returns 502 Bad Gateway

- Ollama service not running
- Start with: `ollama serve`

### Frontend Shows "Failed to get response"

- Check browser console for errors
- Verify auth token is valid
- Check CORS settings in `api/main.py`

### Chat Page Not Loading

- Verify route added to App.tsx
- Check for TypeScript errors: `npm run build`
- Clear browser cache

---

## Performance & Safety

### Model Choice

Current: **llama3.1:8b** (8 billion parameters, quantized)
- Size: ~4.7GB
- Speed: ~10-30 tokens/sec on M1 Mac
- Quality: Good for general chat

Alternatives:
- **llama3.2:3b**: Faster, less accurate
- **llama3.1:70b**: Much slower, more accurate (requires >32GB RAM)

### Safety Considerations

1. **No External API Calls**: LLM runs locally, no data leaves machine
2. **Privacy Redaction**: Use PrivacyService.redact_for_llm() before sharing session data
3. **Authentication Required**: All endpoints require JWT token
4. **No Streaming Initially**: Simpler error handling, can add later
5. **Timeout Protection**: 60s timeout prevents hanging requests
6. **Input Validation**: Pydantic models validate all requests

### Resource Usage

- Ollama: ~6-8GB RAM (llama3.1:8b)
- Backend: ~100MB RAM
- Frontend: ~50MB RAM
- Database: SQLite (minimal overhead)

---

## File Reference

### Backend Files
- `api/routes/chat.py` - Chat proxy endpoint
- `api/routes/llm_tools.py` - Tool contract stubs
- `api/main.py` - Router registration
- `core/services/privacy_service.py` - LLM redaction method
- `requirements.txt` - Added httpx

### Frontend Files
- `web/src/pages/Chat.tsx` - Chat UI component
- `web/src/App.tsx` - Chat route registration

### Documentation
- `CHAT_RUNBOOK.md` - This file

---

## Quick Reference

```bash
# Start everything
brew services start ollama          # Background service
cd rivaflow && uvicorn rivaflow.api.main:app --reload --host 0.0.0.0 --port 8000 &
cd web && npm run dev &

# Test chat
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'

# Check Ollama
ollama list
ollama ps  # Show running models

# Update model
ollama pull llama3.1:8b
```

---

## Next Steps

1. **Add streaming**: Real-time token-by-token responses
2. **Implement tool calling**: Connect LLM to RivaFlow data
3. **Add system prompt**: Guide LLM behavior for BJJ coaching
4. **Conversation persistence**: Save chat history to database
5. **Multi-user context**: LLM sees user's training data
6. **Voice input**: Add speech-to-text for mobile

---

**Status**: ✅ Lightweight chat MVP complete
**Last Updated**: 2026-01-26
