# Quick Start Guide - Backend Services

## Prerequisites Check

✅ PostgreSQL running
✅ Redis running
✅ SKIP_OTP_SENDING=True in .env (for development)

## Start All Services

You need **3 terminals** running simultaneously:

### Terminal 1: Django API Server

```bash
cd /Users/pedmonte/projects/whatsapp-ai
source venv/bin/activate
./venv/bin/python manage.py runserver
```

**What it does**: Handles HTTP requests, serves API endpoints
**URL**: http://localhost:8000
**Logs**: Watch for OTP codes when `SKIP_OTP_SENDING=True`

---

### Terminal 2: Celery Worker

```bash
cd /Users/pedmonte/projects/whatsapp-ai
source venv/bin/activate
./venv/bin/celery -A whatsapp_ai_chatbot worker --loglevel=info
```

**What it does**: Processes async tasks (WhatsApp messages, AI responses)
**Why needed**: Handles message processing in the background

---

### Terminal 3: Celery Beat (Optional for now)

```bash
cd /Users/pedmonte/projects/whatsapp-ai
source venv/bin/activate
./venv/bin/celery -A whatsapp_ai_chatbot beat --loglevel=info
```

**What it does**: Scheduled periodic tasks
**Note**: Not required for basic authentication testing

---

## Quick Verification

Once all services are running:

```bash
# Check Django is up
curl http://localhost:8000/health/

# Should return: {"status": "ok", ...}
```

---

## What You'll See When Testing Login

When a user requests OTP with `SKIP_OTP_SENDING=True`:

**Terminal 1 (Django) output:**
```
⚠️  DEVELOPMENT MODE: Skipping WhatsApp OTP sending
📱 Phone: +12345678900
🔑 OTP: 123456
⏱️  Valid for 5 minutes
```

**Copy the OTP** and paste it into the frontend!

---

## Troubleshooting

### "Address already in use" (port 8000)
```bash
lsof -i :8000
kill <PID>
```

### Redis not responding
```bash
redis-cli ping  # Should return PONG
brew services restart redis
```

### PostgreSQL connection error
```bash
brew services restart postgresql@14
```

### Celery worker not starting
```bash
# Check Redis is running (Celery uses it as broker)
redis-cli ping

# Try with debug logging
./venv/bin/celery -A whatsapp_ai_chatbot worker --loglevel=debug
```

---

## Stop All Services

Press `Ctrl+C` in each terminal window

---

## Next Steps

Once backend is running:
1. Start the frontend: `cd frontend && npm run dev`
2. Open http://localhost:5173
3. Test login with any phone number
4. Copy OTP from Terminal 1 logs
5. You're authenticated! 🎉
