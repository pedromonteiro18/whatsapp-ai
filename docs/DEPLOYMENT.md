# Deployment Guide

This guide covers deploying the WhatsApp AI Chatbot to AWS EC2 instances with CI/CD via GitHub Actions.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [GitHub Configuration](#github-configuration)
- [Deployment Workflow](#deployment-workflow)
- [Manual Operations](#manual-operations)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Architecture Overview

### Environments

- **Beta**: Automatic deployment from `main` branch for testing
- **Production**: Manual approval required after beta deployment

### Infrastructure

Each environment runs on a separate AWS EC2 t3.micro instance ($0.0104/hour) with:

- Docker Compose orchestrating all services
- PostgreSQL database (persistent volume)
- Redis cache (persistent volume)
- Django backend (Gunicorn)
- Celery worker
- Celery beat scheduler
- Nginx reverse proxy + React frontend

### Deployment Flow

```
Developer pushes to main
    ↓
GitHub Actions runs tests
    ↓
Tests pass → Deploy to Beta (automatic)
    ↓
Manual testing in beta
    ↓
Approve in GitHub UI
    ↓
Deploy to Production (automatic after approval)
```

## Prerequisites

### Required Accounts

1. **AWS Account** - For hosting EC2 instances
2. **GitHub Account** - For CI/CD pipelines
3. **Domain** - For beta.yourdomain.com and yourdomain.com
4. **Twilio Account** - For WhatsApp messaging
5. **OpenRouter/OpenAI Account** - For AI responses

### Local Tools

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
sudo apt-get install awscli  # Ubuntu

# Configure AWS credentials
aws configure
```

## Initial Setup

### Step 1: Create EC2 Instances

#### Beta Instance

```bash
# Create t3.micro instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxx \
    --subnet-id subnet-xxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=whatsapp-ai-beta}]' \
    --region us-east-1
```

#### Production Instance

```bash
# Create t3.micro instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxx \
    --subnet-id subnet-xxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=whatsapp-ai-prod}]' \
    --region us-east-1
```

### Step 2: Configure Security Groups

Open these ports:

- **22** (SSH) - Your IP only
- **80** (HTTP) - 0.0.0.0/0
- **443** (HTTPS) - 0.0.0.0/0

```bash
# Create security group
aws ec2 create-security-group \
    --group-name whatsapp-ai-sg \
    --description "Security group for WhatsApp AI Chatbot" \
    --region us-east-1

# Add rules
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxx \
    --protocol tcp --port 22 --cidr your-ip/32 \
    --region us-east-1

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxx \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region us-east-1

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxx \
    --protocol tcp --port 443 --cidr 0.0.0.0/0 \
    --region us-east-1
```

### Step 3: Allocate Elastic IPs

```bash
# Allocate IP for beta
aws ec2 allocate-address --region us-east-1

# Allocate IP for production
aws ec2 allocate-address --region us-east-1

# Associate with instances
aws ec2 associate-address \
    --instance-id i-xxxxxxxxxxxxxxxxx \
    --allocation-id eipalloc-xxxxxxxx \
    --region us-east-1
```

### Step 4: Configure DNS

Add A records in your DNS provider:

- `beta.yourdomain.com` → Beta Elastic IP
- `yourdomain.com` → Production Elastic IP
- `www.yourdomain.com` → Production Elastic IP (optional)

### Step 5: Install Docker on Each Instance

SSH into each instance:

```bash
ssh ubuntu@<elastic-ip>
```

Then install Docker and Docker Compose:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login again for group changes to take effect
exit
```

### Step 6: Clone Repository on Each Instance

```bash
ssh ubuntu@<elastic-ip>

# Create app directory
sudo mkdir -p /app
sudo chown ubuntu:ubuntu /app

# Clone repository
cd /app
git clone https://github.com/yourusername/whatsapp-ai.git
cd whatsapp-ai
```

### Step 7: Configure Environment Variables

On each instance, create `.env` file:

```bash
# Beta instance
cd /app/whatsapp-ai
cp .env.example.beta .env
nano .env  # Edit with your values

# Production instance
cd /app/whatsapp-ai
cp .env.example.prod .env
nano .env  # Edit with your values
```

### Step 8: Install SSL Certificates

On each instance:

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Stop nginx if running
docker-compose -f infrastructure/docker-compose.beta.yml stop nginx

# Get certificate
sudo certbot certonly --standalone -d beta.yourdomain.com

# Certificates are stored in /etc/letsencrypt/live/beta.yourdomain.com/
```

Update `infrastructure/docker-compose.beta.yml` to mount SSL certificates:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

## GitHub Configuration

### Step 1: Create GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

**Beta Secrets:**

- `BETA_HOST`: Beta Elastic IP address
- `BETA_SSH_KEY`: Private SSH key for beta instance
- `BETA_SSH_USER`: `ubuntu`

**Production Secrets:**

- `PROD_HOST`: Production Elastic IP address
- `PROD_SSH_KEY`: Private SSH key for production instance
- `PROD_SSH_USER`: `ubuntu`

### Step 2: Generate SSH Keys for GitHub Actions

On your local machine:

```bash
# Generate new SSH key pair
ssh-keygen -t ed25519 -C "github-actions-beta" -f ~/.ssh/github-actions-beta
ssh-keygen -t ed25519 -C "github-actions-prod" -f ~/.ssh/github-actions-prod

# Copy public keys to instances
ssh-copy-id -i ~/.ssh/github-actions-beta.pub ubuntu@<beta-ip>
ssh-copy-id -i ~/.ssh/github-actions-prod.pub ubuntu@<prod-ip>

# Copy private keys to GitHub secrets
cat ~/.ssh/github-actions-beta  # Copy this to BETA_SSH_KEY
cat ~/.ssh/github-actions-prod  # Copy this to PROD_SSH_KEY
```

### Step 3: Create GitHub Environments

Go to your repository → Settings → Environments

**Create Beta Environment:**

- Name: `beta`
- No protection rules needed (auto-deploy)
- Environment URL: `https://beta.yourdomain.com`

**Create Production Environment:**

- Name: `production`
- Protection rules:
  - ✅ Required reviewers: Add yourself (and team members)
  - ✅ Wait timer: 0 minutes
- Environment URL: `https://yourdomain.com`

### Step 4: Set Up Branch Protection

Go to your repository → Settings → Branches → Add branch protection rule

For `main` branch:

- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - Select: `Test Backend`, `Test Frontend`
- ✅ Require branches to be up to date before merging

## Deployment Workflow

### Automatic Beta Deployment

1. Create feature branch:

```bash
git checkout -b feature/new-feature
```

2. Make changes and commit:

```bash
git add .
git commit -m "Add new feature"
```

3. Push and create PR:

```bash
git push origin feature/new-feature
```

4. Merge PR to `main` via GitHub UI

5. GitHub Actions automatically:
   - Runs tests
   - Deploys to beta (if tests pass)

6. Test in beta: `https://beta.yourdomain.com`

### Manual Production Deployment

After testing in beta:

1. Go to GitHub → Actions → Latest workflow run
2. Scroll to "Deploy to Production" job
3. Click "Review deployments"
4. Select "production" environment
5. Click "Approve and deploy"

Production deployment starts automatically after approval.

## Manual Operations

### Starting/Stopping Instances

**Start Beta Instance:**

```bash
# Update BETA_INSTANCE_ID in scripts/start-beta.sh first
./scripts/start-beta.sh
```

**Stop Beta Instance:**

```bash
./scripts/stop-beta.sh
```

**Start Production Instance:**

```bash
./scripts/start-prod.sh
```

**Stop Production Instance (with confirmation):**

```bash
./scripts/stop-prod.sh
```

### Manual Deployment (SSH Method)

If GitHub Actions fails, deploy manually:

**Beta:**

```bash
ssh ubuntu@<beta-ip>
cd /app/whatsapp-ai
./scripts/deploy-beta.sh
```

**Production:**

```bash
ssh ubuntu@<prod-ip>
cd /app/whatsapp-ai
./scripts/deploy-prod.sh
```

### Viewing Logs

```bash
# SSH into instance
ssh ubuntu@<instance-ip>
cd /app/whatsapp-ai

# View all logs
docker-compose -f infrastructure/docker-compose.beta.yml logs -f

# View specific service logs
docker-compose -f infrastructure/docker-compose.beta.yml logs -f web
docker-compose -f infrastructure/docker-compose.beta.yml logs -f celery_worker

# View Django application logs
docker-compose -f infrastructure/docker-compose.beta.yml exec web tail -f /app/logs/whatsapp_chatbot.log
```

### Database Operations

**Backup Database:**

```bash
ssh ubuntu@<instance-ip>
cd /app/whatsapp-ai

# Backup
docker-compose -f infrastructure/docker-compose.prod.yml exec -T db \
    pg_dump -U postgres whatsapp_chatbot_prod > backup.sql

# Download to local
scp ubuntu@<instance-ip>:/app/whatsapp-ai/backup.sql ./
```

**Restore Database:**

```bash
# Upload backup
scp backup.sql ubuntu@<instance-ip>:/app/whatsapp-ai/

# Restore
ssh ubuntu@<instance-ip>
cd /app/whatsapp-ai
cat backup.sql | docker-compose -f infrastructure/docker-compose.prod.yml exec -T db \
    psql -U postgres whatsapp_chatbot_prod
```

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. SSH into instance and check logs:

```bash
docker-compose -f infrastructure/docker-compose.beta.yml logs -f
```

3. Verify environment variables:

```bash
cat .env
```

4. Check service status:

```bash
docker-compose -f infrastructure/docker-compose.beta.yml ps
```

### Services Not Starting

```bash
# Restart all services
docker-compose -f infrastructure/docker-compose.beta.yml restart

# Rebuild and restart
docker-compose -f infrastructure/docker-compose.beta.yml up -d --build --force-recreate
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f infrastructure/docker-compose.beta.yml ps db

# Check database logs
docker-compose -f infrastructure/docker-compose.beta.yml logs db

# Restart database
docker-compose -f infrastructure/docker-compose.beta.yml restart db
```

### SSL Certificate Issues

```bash
# Renew certificates (run as root)
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

## Cost Optimization

### Current Costs (Per Month)

**Both Instances Running 24/7:**

- Beta: t3.micro × 730 hours = ~$7.50
- Production: t3.micro × 730 hours = ~$7.50
- EBS storage (30GB each) = ~$6
- **Total: ~$21/month**

**Both Instances Stopped:**

- EBS storage only = ~$6/month

### Optimization Strategies

1. **Stop beta when not testing** (saves ~$7/month):

```bash
./scripts/stop-beta.sh
```

2. **Use spot instances** (save ~50%, but can be interrupted)

3. **Run both on single instance** (save ~$7/month):
   - Use different ports
   - Modify docker-compose to not conflict

4. **Use smaller instance for beta** (save ~$3-4/month):
   - Downgrade beta to t3.micro or t3.nano

5. **Set up auto-shutdown** for beta:

```bash
# Add to crontab on beta instance
0 18 * * 1-5 sudo shutdown -h now  # Shutdown at 6pm weekdays
```

## Health Checks

### Automated Health Checks

The CI/CD pipeline includes health checks:

```bash
curl --fail https://beta.yourdomain.com/health/
```

### Manual Health Check

```bash
# Check all services
docker-compose -f infrastructure/docker-compose.prod.yml ps

# Check specific endpoints
curl https://yourdomain.com/health/
curl https://yourdomain.com/api/activities/
```

## Rollback Procedure

If production deployment fails:

1. SSH into production instance:

```bash
ssh ubuntu@<prod-ip>
cd /app/whatsapp-ai
```

2. Find previous working commit:

```bash
git log --oneline -10
```

3. Rollback to previous commit:

```bash
git checkout <previous-commit-hash>
./scripts/deploy-prod.sh
```

4. Or use docker-compose to rollback:

```bash
# Previous images are tagged, list them:
docker images | grep whatsapp-ai

# Use previous image:
# Edit docker-compose.prod.yml to use specific image tag
docker-compose -f infrastructure/docker-compose.prod.yml up -d
```

## Monitoring

### Set Up Monitoring (Optional)

1. **CloudWatch** (AWS native):
   - EC2 metrics (CPU, memory, disk)
   - Custom metrics (application logs)

2. **Uptime monitoring**:
   - UptimeRobot (free tier)
   - Better Uptime (free tier)

3. **Log aggregation**:
   - CloudWatch Logs
   - Papertrail (free tier)

## Security Best Practices

1. **Rotate secrets regularly** (quarterly):
   - SECRET_KEY
   - Database passwords
   - API keys

2. **Keep system updated**:

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

3. **Monitor access logs**:

```bash
tail -f /var/log/auth.log  # SSH access
```

4. **Use SSH keys only** (disable password auth):

```bash
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

5. **Enable automatic security updates**:

```bash
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## Next Steps

After successful deployment:

1. Set up monitoring and alerting
2. Configure automated backups
3. Set up log rotation
4. Document runbooks for common issues
5. Set up staging environment (optional)
6. Implement blue-green deployment (advanced)
