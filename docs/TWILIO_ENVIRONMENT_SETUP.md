# Twilio Multi-Environment Setup Guide

This document explains how to configure separate Twilio subaccounts for beta and production environments.

## Overview

The WhatsApp AI chatbot uses **separate Twilio subaccounts** for beta and production environments:

- **Beta Subaccount**: Used for testing and development
- **Production Subaccount**: Used for live users

Each subaccount has:
- Its own credentials (Account SID and Auth Token)
- Its own WhatsApp phone number
- Separate usage tracking and billing
- Isolated webhook configuration

## Architecture

```
Main Twilio Account
├── Beta Subaccount (AC_beta_xxx)
│   ├── Credentials: BETA_TWILIO_ACCOUNT_SID, BETA_TWILIO_AUTH_TOKEN
│   ├── Phone Number: whatsapp:+1XXXXXXXXXX (beta number)
│   └── Webhook: https://resort-booking-beta.duckdns.org/whatsapp/webhook/
│
└── Production Subaccount (AC_prod_xxx)
    ├── Credentials: PROD_TWILIO_ACCOUNT_SID, PROD_TWILIO_AUTH_TOKEN
    ├── Phone Number: whatsapp:+1YYYYYYYYYY (prod number)
    └── Webhook: https://resort-booking.duckdns.org/whatsapp/webhook/
```

## Step 1: Create Twilio Subaccounts

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to **Account → Subaccounts**
3. Click **Create new Subaccount**

### Create Beta Subaccount
- **Friendly Name**: `WhatsApp AI Bot - Beta`
- **Description**: `Beta testing environment for WhatsApp chatbot`
- Note down the **Account SID** (starts with `AC`)
- Note down the **Auth Token**

### Create Production Subaccount
- **Friendly Name**: `WhatsApp AI Bot - Production`
- **Description**: `Production environment for WhatsApp chatbot`
- Note down the **Account SID** (starts with `AC`)
- Note down the **Auth Token**

## Step 2: Configure WhatsApp Numbers

### Beta Subaccount
1. Switch to beta subaccount in Twilio Console
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Follow Twilio's sandbox setup or purchase a dedicated WhatsApp number
4. Note the number in format: `whatsapp:+14155238886`

### Production Subaccount
1. Switch to production subaccount in Twilio Console
2. Purchase a dedicated WhatsApp-enabled phone number
3. Complete WhatsApp Business Profile setup
4. Note the number in format: `whatsapp:+15551234567`

## Step 3: Configure Webhooks in Twilio Console

### Beta Webhook Configuration
1. Switch to **beta subaccount** in Twilio Console
2. Go to **Messaging → Settings → WhatsApp sandbox settings** (or number settings)
3. Set **"When a message comes in"** webhook to:
   ```
   https://resort-booking-beta.duckdns.org/whatsapp/webhook/
   ```
4. Method: **HTTP POST**
5. Click **Save**

### Production Webhook Configuration
1. Switch to **production subaccount** in Twilio Console
2. Go to **Phone Numbers → Manage → Active Numbers**
3. Click on your WhatsApp number
4. Scroll to **Messaging Configuration**
5. Set **"A message comes in"** webhook to:
   ```
   https://resort-booking.duckdns.org/whatsapp/webhook/
   ```
6. Method: **HTTP POST**
7. Click **Save**

## Step 4: Add Secrets to GitHub

### Using GitHub Web UI

1. Go to your repository: `https://github.com/[username]/whatsapp-ai`
2. Click **Settings → Environments**

#### Configure Beta Environment
3. Click on **beta** environment
4. Under **Environment secrets**, add:
   - `BETA_TWILIO_ACCOUNT_SID`: Your beta Account SID (e.g., `ACxxxxxxxxxxxxxxxxxxxx`)
   - `BETA_TWILIO_AUTH_TOKEN`: Your beta Auth Token
   - `BETA_TWILIO_WHATSAPP_NUMBER`: Beta WhatsApp number (e.g., `whatsapp:+14155238886`)

#### Configure Production Environment
5. Click on **production** environment
6. Under **Environment secrets**, add:
   - `PROD_TWILIO_ACCOUNT_SID`: Your prod Account SID
   - `PROD_TWILIO_AUTH_TOKEN`: Your prod Auth Token
   - `PROD_TWILIO_WHATSAPP_NUMBER`: Prod WhatsApp number (e.g., `whatsapp:+15551234567`)

### Using GitHub CLI (Alternative)

```bash
# Install GitHub CLI if needed
brew install gh

# Authenticate
gh auth login

# Navigate to your project
cd /path/to/whatsapp-ai

# Add beta secrets
gh secret set BETA_TWILIO_ACCOUNT_SID --env beta --body "ACxxxxxxxxxxxxxxxxxxxx"
gh secret set BETA_TWILIO_AUTH_TOKEN --env beta --body "your_beta_auth_token"
gh secret set BETA_TWILIO_WHATSAPP_NUMBER --env beta --body "whatsapp:+14155238886"

# Add production secrets
gh secret set PROD_TWILIO_ACCOUNT_SID --env production --body "ACyyyyyyyyyyyyyyyyyyyy"
gh secret set PROD_TWILIO_AUTH_TOKEN --env production --body "your_prod_auth_token"
gh secret set PROD_TWILIO_WHATSAPP_NUMBER --env production --body "whatsapp:+15551234567"
```

## Step 5: Update Server .env Files (Manual)

After deployment runs, the CI/CD pipeline will automatically update the `.env` files on your servers. However, for the **first deployment**, you should manually set the correct credentials on each server.

### Beta Server

SSH into beta server:
```bash
ssh ubuntu@[BETA_SERVER_IP]
cd /app/whatsapp-ai
```

Edit `.env` and ensure these lines are set correctly:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx  # Beta Account SID
TWILIO_AUTH_TOKEN=your_beta_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Beta number
```

Restart services:
```bash
docker-compose -f infrastructure/docker-compose.beta.yml restart
```

### Production Server

SSH into production server:
```bash
ssh ubuntu@[PROD_SERVER_IP]
cd /app/whatsapp-ai
```

Edit `.env` and ensure these lines are set correctly:
```bash
TWILIO_ACCOUNT_SID=ACyyyyyyyyyyyyyyyyyyyy  # Prod Account SID
TWILIO_AUTH_TOKEN=your_prod_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+15551234567  # Prod number
```

Restart services:
```bash
docker-compose -f infrastructure/docker-compose.prod.yml restart
```

## Step 6: Verify Configuration

### Test Beta Environment

1. Send a WhatsApp message to your **beta number**
2. Check beta server logs:
   ```bash
   ssh ubuntu@[BETA_SERVER_IP]
   cd /app/whatsapp-ai
   docker-compose -f infrastructure/docker-compose.beta.yml logs -f web
   ```
3. Verify webhook receives message and processes correctly

### Test Production Environment

1. Send a WhatsApp message to your **production number**
2. Check production server logs:
   ```bash
   ssh ubuntu@[PROD_SERVER_IP]
   cd /app/whatsapp-ai
   docker-compose -f infrastructure/docker-compose.prod.yml logs -f web
   ```
3. Verify webhook receives message and processes correctly

## How It Works

### During Deployment

When you push to `main` branch, the CI/CD workflow:

1. **Builds** Docker images for both frontend and backend
2. **Deploys to Beta** first:
   - Pulls latest code
   - **Injects beta Twilio credentials** into `.env` using `sed`
   - Pulls pre-built Docker images
   - Restarts all services
   - Runs migrations
3. **Deploys to Production** (after beta succeeds):
   - Pulls latest code
   - **Injects production Twilio credentials** into `.env` using `sed`
   - Pulls pre-built Docker images
   - Restarts all services
   - Runs migrations

### Security Best Practices

✅ **Good:**
- Separate credentials per environment
- Credentials stored as GitHub secrets (encrypted at rest)
- Credentials injected during deployment (never committed to git)
- Each environment has isolated billing and usage tracking

❌ **Never:**
- Commit `.env` files to git
- Share credentials between environments
- Use production credentials in beta
- Hardcode credentials in code

## Troubleshooting

### Webhook Not Receiving Messages

**Check webhook configuration in Twilio:**
1. Go to Twilio Console → Switch to correct subaccount
2. Check webhook URL is set correctly
3. Verify webhook URL is accessible (health check endpoint: `https://[domain]/health/`)

**Check server logs:**
```bash
# Beta
ssh ubuntu@[BETA_IP]
docker-compose -f infrastructure/docker-compose.beta.yml logs -f web

# Production
ssh ubuntu@[PROD_IP]
docker-compose -f infrastructure/docker-compose.prod.yml logs -f web
```

### Wrong Phone Number Displayed

If users see the wrong phone number, verify:
1. Correct subaccount credentials are set in server `.env`
2. Services were restarted after changing credentials
3. GitHub secrets are set correctly for the environment

### Deployment Fails with "sed: invalid reference"

This means the `sed` command couldn't find the Twilio configuration lines in `.env`. Ensure:
1. Server `.env` file exists at `/app/whatsapp-ai/.env`
2. `.env` contains lines starting with `TWILIO_ACCOUNT_SID=`, `TWILIO_AUTH_TOKEN=`, `TWILIO_WHATSAPP_NUMBER=`
3. Lines are not commented out with `#`

## Reference: Complete Environment Variables

### Beta Server `.env`
```bash
# ... other config ...

# Twilio Configuration (Beta Subaccount)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_beta_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# ... other config ...
```

### Production Server `.env`
```bash
# ... other config ...

# Twilio Configuration (Production Subaccount)
TWILIO_ACCOUNT_SID=ACyyyyyyyyyyyyyyyyyyyy
TWILIO_AUTH_TOKEN=your_prod_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+15551234567

# ... other config ...
```

## Next Steps

After completing this setup:

1. ✅ Test beta environment thoroughly
2. ✅ Set up WhatsApp Business Profile for production number (name, logo, description)
3. ✅ Configure rate limits in Twilio (different for beta vs prod)
4. ✅ Set up monitoring/alerts for webhook failures
5. ✅ Update internal documentation with phone numbers for testing
