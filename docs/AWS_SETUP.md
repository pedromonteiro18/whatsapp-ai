# AWS EC2 Setup Guide

Step-by-step guide for setting up AWS EC2 instances for the WhatsApp AI Chatbot.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Creating EC2 Instances](#creating-ec2-instances)
- [Security Configuration](#security-configuration)
- [Elastic IP Setup](#elastic-ip-setup)
- [Instance Configuration](#instance-configuration)
- [Cost Management](#cost-management)

## Prerequisites

### AWS Account Setup

1. Create AWS account at <https://aws.amazon.com>
2. Set up billing alerts:
   - Go to Billing Dashboard
   - Create budget alert for $20/month
   - Set up email notifications

### Install AWS CLI

**macOS:**

```bash
brew install awscli
```

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install awscli
```

**Windows:**
Download from <https://aws.amazon.com/cli/>

### Configure AWS Credentials

```bash
aws configure
```

Enter when prompted:

- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

## Creating EC2 Instances

### Step 1: Choose Region

Choose a region close to your users:

- **us-east-1** (N. Virginia) - Default, lowest cost
- **us-west-2** (Oregon) - West coast US
- **eu-west-1** (Ireland) - Europe
- **ap-southeast-1** (Singapore) - Asia

### Step 2: Create Key Pair

```bash
# Create key pair
aws ec2 create-key-pair \
    --key-name whatsapp-ai-key \
    --query 'KeyMaterial' \
    --output text \
    --region us-east-1 > ~/whatsapp-ai-key.pem

# Set permissions
chmod 400 ~/whatsapp-ai-key.pem
```

### Step 3: Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
    --group-name whatsapp-ai-sg \
    --description "Security group for WhatsApp AI Chatbot" \
    --region us-east-1

# Note the security group ID from output (sg-xxxxxxxxx)
SECURITY_GROUP_ID="sg-xxxxxxxxx"

# Add SSH rule (replace YOUR_IP with your actual IP)
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32 \
    --region us-east-1

# Add HTTP rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region us-east-1

# Add HTTPS rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

### Step 4: Launch Beta Instance

```bash
# Get latest Ubuntu 22.04 AMI ID
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text \
    --region us-east-1)

echo "Using AMI: $AMI_ID"

# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t3.micro \
    --key-name whatsapp-ai-key \
    --security-group-ids $SECURITY_GROUP_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=whatsapp-ai-beta},{Key=Environment,Value=beta}]' \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3,DeleteOnTermination=false}' \
    --region us-east-1

# Note the instance ID from output (i-xxxxxxxxxxxxxxxxx)
BETA_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
```

### Step 5: Launch Production Instance

```bash
# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t3.micro \
    --key-name whatsapp-ai-key \
    --security-group-ids $SECURITY_GROUP_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=whatsapp-ai-prod},{Key=Environment,Value=production}]' \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3,DeleteOnTermination=false}' \
    --region us-east-1

# Note the instance ID from output
PROD_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
```

### Step 6: Wait for Instances to Start

```bash
# Wait for beta instance
aws ec2 wait instance-running \
    --instance-ids $BETA_INSTANCE_ID \
    --region us-east-1

# Wait for production instance
aws ec2 wait instance-running \
    --instance-ids $PROD_INSTANCE_ID \
    --region us-east-1

echo "Instances are running!"
```

## Elastic IP Setup

Elastic IPs provide static IP addresses that persist even when instances are stopped.

### Allocate Elastic IPs

```bash
# Allocate for beta
BETA_ALLOCATION=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=whatsapp-ai-beta-eip}]' \
    --query 'AllocationId' \
    --output text \
    --region us-east-1)

echo "Beta Elastic IP Allocation ID: $BETA_ALLOCATION"

# Allocate for production
PROD_ALLOCATION=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=whatsapp-ai-prod-eip}]' \
    --query 'AllocationId' \
    --output text \
    --region us-east-1)

echo "Production Elastic IP Allocation ID: $PROD_ALLOCATION"
```

### Associate with Instances

```bash
# Associate beta Elastic IP
aws ec2 associate-address \
    --instance-id $BETA_INSTANCE_ID \
    --allocation-id $BETA_ALLOCATION \
    --region us-east-1

# Associate production Elastic IP
aws ec2 associate-address \
    --instance-id $PROD_INSTANCE_ID \
    --allocation-id $PROD_ALLOCATION \
    --region us-east-1
```

### Get Elastic IP Addresses

```bash
# Get beta IP
BETA_IP=$(aws ec2 describe-addresses \
    --allocation-ids $BETA_ALLOCATION \
    --query 'Addresses[0].PublicIp' \
    --output text \
    --region us-east-1)

echo "Beta IP: $BETA_IP"

# Get production IP
PROD_IP=$(aws ec2 describe-addresses \
    --allocation-ids $PROD_ALLOCATION \
    --query 'Addresses[0].PublicIp' \
    --output text \
    --region us-east-1)

echo "Production IP: $PROD_IP"
```

## Instance Configuration

### Step 1: Connect to Instance

```bash
# Connect to beta
ssh -i ~/whatsapp-ai-key.pem ubuntu@$BETA_IP

# Connect to production (in separate terminal)
ssh -i ~/whatsapp-ai-key.pem ubuntu@$PROD_IP
```

### Step 2: Update System

Run on each instance:

```bash
# Update package list
sudo apt-get update

# Upgrade packages
sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip
```

### Step 3: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Test Docker
docker --version
```

### Step 4: Install Docker Compose

```bash
# Download latest version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Test Docker Compose
docker-compose --version
```

### Step 5: Set Up Application Directory

```bash
# Create app directory
sudo mkdir -p /app
sudo chown ubuntu:ubuntu /app

# Create logs directory
sudo mkdir -p /var/log/whatsapp-ai
sudo chown ubuntu:ubuntu /var/log/whatsapp-ai
```

### Step 6: Configure Firewall (UFW)

```bash
# Install UFW
sudo apt-get install -y ufw

# Set defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

### Step 7: Set Up Automatic Updates

```bash
# Install unattended-upgrades
sudo apt-get install -y unattended-upgrades

# Configure
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Enable automatic reboots (if needed)
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
# Uncomment: Unattended-Upgrade::Automatic-Reboot "true";
```

### Step 8: Configure Swap (Optional, for t3.micro)

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

## Cost Management

### Current Costs

**Per Instance (t3.micro):**

- Instance (running): $0.0104/hour = ~$7.50/month
- EBS Storage (30GB gp3): $0.08/GB/month = ~$2.40/month
- Elastic IP (when instance running): $0/month
- Elastic IP (when instance stopped): $0.005/hour = ~$3.60/month
- **Total running**: ~$10/month per instance
- **Total stopped**: ~$6/month per instance (storage + EIP only)

### Cost Optimization Tips

1. **Stop instances when not in use:**

```bash
# Stop instance
aws ec2 stop-instances --instance-ids $BETA_INSTANCE_ID

# Start instance
aws ec2 start-instances --instance-ids $BETA_INSTANCE_ID
```

2. **Use Reserved Instances** (save ~40%):
   - Commit to 1 or 3 years
   - Pay upfront for discount
   - Good for production if running 24/7

3. **Use Spot Instances** (save ~70%):
   - Can be interrupted
   - Good for beta/development
   - Not recommended for production

4. **Set up billing alerts:**

```bash
# Via AWS CLI
aws budgets create-budget \
    --account-id YOUR_ACCOUNT_ID \
    --budget file://budget.json \
    --notifications-with-subscribers file://notifications.json
```

5. **Schedule automatic start/stop:**
   - Use AWS Lambda + CloudWatch Events
   - Start beta at 9am weekdays
   - Stop beta at 6pm weekdays
   - Saves ~60% on beta costs

### Monitoring Costs

**Check current month costs:**

```bash
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=SERVICE
```

**Set up billing alarm:**

1. Go to CloudWatch console
2. Create alarm for "EstimatedCharges"
3. Set threshold (e.g., $20)
4. Add email notification

## Helpful Commands

### List Instances

```bash
# List all instances
aws ec2 describe-instances \
    --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
    --output table \
    --region us-east-1
```

### Get Instance Info

```bash
# Get instance details
aws ec2 describe-instances \
    --instance-ids $BETA_INSTANCE_ID \
    --region us-east-1
```

### Update Security Group

```bash
# Add new rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region us-east-1

# Remove rule
aws ec2 revoke-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

### Create AMI Backup

```bash
# Create AMI of running instance
aws ec2 create-image \
    --instance-id $PROD_INSTANCE_ID \
    --name "whatsapp-ai-prod-backup-$(date +%Y%m%d)" \
    --description "Production backup created on $(date)" \
    --region us-east-1
```

### Terminate Instance (CAREFUL!)

```bash
# Terminate instance (WARNING: This deletes the instance!)
aws ec2 terminate-instances \
    --instance-ids $BETA_INSTANCE_ID \
    --region us-east-1

# To prevent termination, enable termination protection:
aws ec2 modify-instance-attribute \
    --instance-id $PROD_INSTANCE_ID \
    --disable-api-termination \
    --region us-east-1
```

## Troubleshooting

### Can't Connect via SSH

1. Check security group allows your IP:

```bash
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region us-east-1
```

2. Verify instance is running:

```bash
aws ec2 describe-instance-status \
    --instance-ids $BETA_INSTANCE_ID \
    --region us-east-1
```

3. Check SSH key permissions:

```bash
chmod 400 ~/whatsapp-ai-key.pem
```

### Instance Won't Start

1. Check instance limits (you may have hit your account limit)
2. Check for service health issues in AWS console
3. Try stopping and starting again:

```bash
aws ec2 stop-instances --instance-ids $BETA_INSTANCE_ID
aws ec2 wait instance-stopped --instance-ids $BETA_INSTANCE_ID
aws ec2 start-instances --instance-ids $BETA_INSTANCE_ID
```

### High Costs

1. Check for unattached EBS volumes:

```bash
aws ec2 describe-volumes \
    --filters "Name=status,Values=available" \
    --region us-east-1
```

2. Check for unused Elastic IPs:

```bash
aws ec2 describe-addresses \
    --filters "Name=association.association-id,Values=null" \
    --region us-east-1
```

3. Review CloudWatch metrics for actual usage

## Next Steps

1. Configure DNS records pointing to Elastic IPs
2. Install SSL certificates (see DEPLOYMENT.md)
3. Clone repository and set up application
4. Configure GitHub Actions secrets
5. Test deployment pipeline

## Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Cost Calculator](https://calculator.aws/)
