# Serveo Setup for Remote Testing

## What is Serveo?

Serveo creates a secure SSH tunnel to expose your local Django server to the internet. This is useful for:
- Testing Twilio webhooks
- Testing WhatsApp message reception
- Sharing your local dev server with others

**No installation required** - uses SSH!

---

## Current Setup

- Django is running on port **8001** (not 8000!)
- Backend URL: http://localhost:8001

---

## Step 1: Start Serveo Tunnel

In a **new terminal** (Terminal 4):

```bash
ssh -o StrictHostKeyChecking=no -R 80:localhost:8001 serveo.net
```

You'll see output like:
```
Forwarding HTTP traffic from https://abc123xyz.serveo.net
```

**Copy that URL!** (e.g., `abc123xyz.serveo.net`)

---

## Step 2: Update Django ALLOWED_HOSTS

1. Open `.env` file
2. Find `ALLOWED_HOSTS` line
3. Add the Serveo domain:
   ```bash
   ALLOWED_HOSTS=localhost,127.0.0.1,abc123xyz.serveo.net
   ```

4. **Restart Django** (CRITICAL!):
   - Find Django terminal
   - Press `Ctrl+C`
   - Run: `./venv/bin/python manage.py runserver 0.0.0.0:8001`

---

## Step 3: Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate: **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Scroll to **Sandbox Configuration**
4. Set webhook URL to:
   ```
   https://abc123xyz.serveo.net/api/whatsapp/webhook/
   ```
5. Method: **POST**
6. Click **Save**

---

## Step 4: Test Webhook

Send a WhatsApp message to your Twilio number. You should see:
- Request logged in Django terminal
- Message processed by Celery worker
- AI response sent back via WhatsApp

---

## Important Notes

⚠️ **Serveo URLs change on every restart**
- Keep Serveo terminal open while testing
- Update `.env` ALLOWED_HOSTS each time
- Update Twilio webhook each time
- **Always restart Django after changing ALLOWED_HOSTS**

⚠️ **For authentication testing**
- Frontend still connects to `http://localhost:8001`
- Serveo is only for Twilio → Django webhooks
- Update `frontend/.env`: `VITE_API_URL=http://localhost:8001/api/v1`

---

## Troubleshooting

### "Invalid HTTP_HOST header"
```
Solution: Add Serveo domain to ALLOWED_HOSTS and restart Django
```

### Serveo connection drops
```
Solution: Just restart the SSH command - you'll get a new URL
```

### Twilio webhook timeouts
```
Solution:
1. Check Django is accessible: curl https://your-serveo-url.serveo.net/health/
2. Check Serveo tunnel is running
3. Verify ALLOWED_HOSTS includes Serveo domain
```

---

## Alternative: For Development Only

If you just want to test the **frontend authentication**:
- Skip Serveo entirely
- Use `SKIP_OTP_SENDING=True` (already set!)
- OTPs appear in Django terminal logs
- No Twilio/WhatsApp involved

This is perfect for rapid frontend development!
