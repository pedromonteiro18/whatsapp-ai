# Development Authentication Guide

## Skip OTP Sending During Development

To avoid Twilio costs and rate limits during local development, you can bypass the actual WhatsApp message sending.

### Setup

1. **Enable Development Mode** (already done):
   ```bash
   # In your .env file
   SKIP_OTP_SENDING=True
   ```

2. **Restart Django Server**:
   ```bash
   # Stop current server (Ctrl+C)
   ./venv/bin/python backend/manage.py runserver
   ```

### How It Works

When `SKIP_OTP_SENDING=True`:

1. **User requests OTP** from the frontend
2. **Backend generates OTP** and stores in Redis (normal behavior)
3. **OTP is logged to console** instead of sending via WhatsApp:
   ```
   ⚠️  DEVELOPMENT MODE: Skipping WhatsApp OTP sending
   📱 Phone: +12345678900
   🔑 OTP: 742891
   ⏱️  Valid for 5 minutes
   ```
4. **Copy the OTP from the console** and paste into the frontend
5. **Verification works normally** - the OTP is validated against Redis

### Example Workflow

```bash
# Terminal 1: Start Django server
./venv/bin/python backend/manage.py runserver

# Output when user requests OTP:
# [WARNING] ⚠️  DEVELOPMENT MODE: Skipping WhatsApp OTP sending
# [WARNING] 📱 Phone: +12345678900
# [WARNING] 🔑 OTP: 123456
# [WARNING] ⏱️  Valid for 5 minutes
```

Then in the frontend:
1. Enter phone number: `+12345678900`
2. Click "Send Verification Code"
3. Copy OTP from server logs: `123456`
4. Paste into OTP input and verify

### Production Deployment

**CRITICAL**: Never set `SKIP_OTP_SENDING=True` in production!

For production, either:
- Set `SKIP_OTP_SENDING=False` in `.env`
- Remove the variable entirely (defaults to `False`)

### Why This Approach?

✅ **Advantages**:
- No Twilio API calls during development
- No message costs during testing
- No rate limiting issues
- Test authentication flow without phone access
- Faster iteration (no waiting for messages)

✅ **Still Tests**:
- OTP generation logic
- Redis storage and expiration
- Rate limiting
- Session management
- Frontend authentication flow

❌ **Doesn't Test**:
- Twilio API integration
- WhatsApp message delivery
- Phone number validation by Twilio
- Network resilience

### Testing Twilio Integration

When you need to test the actual Twilio integration:

```bash
# Temporarily disable skip flag
SKIP_OTP_SENDING=False ./venv/bin/python backend/manage.py runserver
```

Or use the management command:
```bash
./venv/bin/python backend/manage.py test_whatsapp --to "+1234567890" --message "Test"
```

### Troubleshooting

**OTP not showing in logs?**
- Check `.env` has `SKIP_OTP_SENDING=True`
- Restart Django server after changing `.env`
- Check log level is set to WARNING or higher

**Frontend shows "Failed to send OTP"?**
- Check Redis is running: `redis-cli ping` should return `PONG`
- Check rate limiting: wait 10 minutes and try again
- Check Django logs for detailed error messages
