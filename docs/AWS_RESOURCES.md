# AWS Resources - WhatsApp AI Chatbot

This document contains information about AWS-managed database resources for the WhatsApp AI Chatbot project.

## Overview

All resources are deployed in **us-east-1** region using the **pedro-personal** AWS profile.

## Beta Environment

### EC2 Instance
- **Instance ID**: `i-0186d19da785a6013`
- **Name**: `whatsapp-ai-beta`
- **Private IP**: `172.31.25.237`
- **Security Groups**:
  - `sg-08badb789772b9609` (whatsapp-ai-beta-ec2-sg - HTTP/HTTPS/SSH access)
  - `sg-096277a1637198282` (Beta-specific rules)

### RDS PostgreSQL
- **Instance ID**: `whatsapp-ai-beta-db`
- **Instance Class**: db.t3.micro
- **Engine**: PostgreSQL 17.2
- **Database Name**: `whatsapp_chatbot`
- **Username**: `postgres`
- **Password**: `BetaPass123!`
- **Storage**: 20GB (encrypted)
- **Backup Retention**: 7 days
- **Public Access**: **Disabled** (VPC-internal only)
- **Security Groups**:
  - `sg-035aa6a4975d73170` (whatsapp-ai-beta-db-sg)
  - `sg-0be209b924a2e5c1e` (manually added via console)
- **Subnet Group**: `whatsapp-ai-beta-subnet-group`
- **Availability Zone**: us-east-1d
- **Tags**:
  - Environment: beta
  - Project: whatsapp-ai

**Endpoint:**
```
whatsapp-ai-beta-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com:5432
```

**Connection String:**
```
postgresql://postgres:BetaPass123!@whatsapp-ai-beta-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com:5432/whatsapp_chatbot
```

### ElastiCache Redis
- **Cluster ID**: `whatsapp-ai-beta-redis`
- **Node Type**: cache.t3.micro
- **Engine**: Redis 7.1.0
- **Nodes**: 1
- **Public Access**: **Not Available** (ElastiCache is always VPC-internal)
- **Security Group**: `sg-035aa6a4975d73170` (whatsapp-ai-beta-db-sg)
- **Subnet Group**: `whatsapp-ai-beta-cache-subnet`
- **Availability Zone**: us-east-1d
- **Auth Token**: Disabled
- **Encryption**: At-rest and in-transit disabled
- **Tags**:
  - Environment: beta
  - Project: whatsapp-ai

**Endpoint:**
```
whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com:6379
```

**Connection String:**
```
redis://whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
```

---

## Production Environment

### EC2 Instance
- **Instance ID**: `i-0b14158e0e93f8e98`
- **Name**: `whatsapp-ai-prod`
- **Private IP**: `172.31.19.155`
- **Security Groups**:
  - `sg-01b8c4b1d3787395d` (whatsapp-ai-prod-ec2-sg - HTTP/HTTPS/SSH access)
  - `sg-0f0360cba0abda5cb` (Prod-specific rules)

### RDS PostgreSQL
- **Instance ID**: `whatsapp-ai-prod-db`
- **Instance Class**: db.t3.micro
- **Engine**: PostgreSQL 17.2
- **Database Name**: `whatsapp_chatbot`
- **Username**: `postgres`
- **Password**: `ProdPass123!`
- **Storage**: 20GB (encrypted)
- **Backup Retention**: 7 days
- **Public Access**: **Disabled** (VPC-internal only)
- **Security Groups**:
  - `sg-0fb2881f61aa47d28` (whatsapp-ai-prod-db-sg)
  - `sg-0084b8967d307b222` (manually added via console)
- **Subnet Group**: `whatsapp-ai-prod-subnet-group`
- **Availability Zone**: us-east-1f
- **Tags**:
  - Environment: production
  - Project: whatsapp-ai

**Endpoint:**
```
whatsapp-ai-prod-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com:5432
```

**Connection String:**
```
postgresql://postgres:ProdPass123!@whatsapp-ai-prod-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com:5432/whatsapp_chatbot
```

### ElastiCache Redis
- **Cluster ID**: `whatsapp-ai-prod-redis`
- **Node Type**: cache.t3.micro
- **Engine**: Redis 7.1.0
- **Nodes**: 1
- **Public Access**: **Not Available** (ElastiCache is always VPC-internal)
- **Security Group**: `sg-0fb2881f61aa47d28` (whatsapp-ai-prod-db-sg)
- **Subnet Group**: `whatsapp-ai-prod-cache-subnet`
- **Availability Zone**: us-east-1e
- **Auth Token**: Disabled
- **Encryption**: At-rest and in-transit disabled
- **Tags**:
  - Environment: production
  - Project: whatsapp-ai

**Endpoint:**
```
whatsapp-ai-prod-redis.nzvdck.0001.use1.cache.amazonaws.com:6379
```

**Connection String:**
```
redis://whatsapp-ai-prod-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
```

---

## Security Groups

### Beta EC2 Security Group
- **ID**: `sg-08badb789772b9609`
- **Name**: `whatsapp-ai-beta-ec2-sg`
- **Description**: Security group for WhatsApp AI Beta EC2 instance
- **Ingress Rules**:
  - SSH (22): From `62.197.36.152/32` and `0.0.0.0/0` (GitHub Actions)
  - HTTP (80): From `0.0.0.0/0`
  - HTTPS (443): From `0.0.0.0/0`
- **Tags**:
  - Environment: beta
  - Project: whatsapp-ai
  - awsApplication: arn:aws:resource-groups:us-east-1:482397319362:group/whatsapp-ai-beta/050swmcztjeoeq3bmgrevlmryb

### Production EC2 Security Group
- **ID**: `sg-01b8c4b1d3787395d`
- **Name**: `whatsapp-ai-prod-ec2-sg`
- **Description**: Security group for WhatsApp AI Prod EC2 instance
- **Ingress Rules**:
  - SSH (22): From `62.197.36.152/32` and `0.0.0.0/0` (GitHub Actions)
  - HTTP (80): From `0.0.0.0/0`
  - HTTPS (443): From `0.0.0.0/0`
- **Tags**:
  - Environment: production
  - Project: whatsapp-ai
  - awsApplication: arn:aws:resource-groups:us-east-1:482397319362:group/whatsapp-ai-production/050t0cw0aqgww7q36iq1o7jb2m

### Beta Database Security Group
- **ID**: `sg-035aa6a4975d73170`
- **Name**: `whatsapp-ai-beta-db-sg`
- **Description**: Security group for WhatsApp AI Beta database resources
- **Ingress Rules**:
  - PostgreSQL (5432): `0.0.0.0/0` (initially created for public access)
  - Redis (6379): `0.0.0.0/0` (initially created, but ElastiCache is VPC-internal only)
  - Redis (6379): From `sg-096277a1637198282` (Beta EC2 security group)

### Production Database Security Group
- **ID**: `sg-0fb2881f61aa47d28`
- **Name**: `whatsapp-ai-prod-db-sg`
- **Description**: Security group for WhatsApp AI Prod database resources
- **Ingress Rules**:
  - PostgreSQL (5432): `0.0.0.0/0` (initially created for public access)
  - Redis (6379): `0.0.0.0/0` (initially created, but ElastiCache is VPC-internal only)
  - Redis (6379): From `sg-0f0360cba0abda5cb` (Prod EC2 security group)

### Network Architecture

**VPC-Internal Communication (Current Setup):**
```
Beta EC2 (sg-08badb789772b9609 + sg-096277a1637198282)
   ├─→ Beta RDS (sg-035aa6a4975d73170 + sg-0be209b924a2e5c1e) ✅
   └─→ Beta Redis (sg-035aa6a4975d73170) ✅

Prod EC2 (sg-01b8c4b1d3787395d + sg-0f0360cba0abda5cb)
   ├─→ Prod RDS (sg-0fb2881f61aa47d28 + sg-0084b8967d307b222) ✅
   └─→ Prod Redis (sg-0fb2881f61aa47d28) ✅
```

**Key Points:**
- **Complete Environment Isolation**: Each environment now has dedicated security groups with no shared resources
- **Beta Environment**: Uses `sg-08badb789772b9609` (EC2 access) + `sg-096277a1637198282` (environment-specific rules)
- **Prod Environment**: Uses `sg-01b8c4b1d3787395d` (EC2 access) + `sg-0f0360cba0abda5cb` (environment-specific rules)
- RDS instances have **public accessibility disabled** (VPC-internal only)
- ElastiCache Redis is **always VPC-internal** (cannot be made public)
- EC2 → Database communication happens privately within the VPC
- Additional security groups manually added via console provide EC2 connectivity
- Both environments now show equal resource counts in AWS Service Catalog myApplications

---

## Resource Status Check

### Check All Resources
```bash
# Beta RDS
aws rds describe-db-instances \
  --profile pedro-personal \
  --region us-east-1 \
  --db-instance-identifier whatsapp-ai-beta-db \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address,Endpoint.Port]' \
  --output table

# Prod RDS
aws rds describe-db-instances \
  --profile pedro-personal \
  --region us-east-1 \
  --db-instance-identifier whatsapp-ai-prod-db \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address,Endpoint.Port]' \
  --output table

# Beta Redis
aws elasticache describe-cache-clusters \
  --profile pedro-personal \
  --region us-east-1 \
  --cache-cluster-id whatsapp-ai-beta-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].[CacheClusterStatus,CacheNodes[0].Endpoint.Address,CacheNodes[0].Endpoint.Port]' \
  --output table

# Prod Redis
aws elasticache describe-cache-clusters \
  --profile pedro-personal \
  --region us-east-1 \
  --cache-cluster-id whatsapp-ai-prod-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].[CacheClusterStatus,CacheNodes[0].Endpoint.Address,CacheNodes[0].Endpoint.Port]' \
  --output table
```

---

## Environment Variable Configuration

Once the resources are available, update your environment files:

### Beta Environment (`.env.beta`)
```bash
# Database
DB_HOST=whatsapp-ai-beta-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=whatsapp_chatbot
DB_USER=postgres
DB_PASSWORD=BetaPass123!

# Redis
REDIS_HOST=whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
```

### Production Environment (`.env.prod`)
```bash
# Database
DB_HOST=whatsapp-ai-prod-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=whatsapp_chatbot
DB_USER=postgres
DB_PASSWORD=ProdPass123!

# Redis
REDIS_HOST=whatsapp-ai-prod-redis.nzvdck.0001.use1.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://whatsapp-ai-prod-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://whatsapp-ai-prod-redis.nzvdck.0001.use1.cache.amazonaws.com:6379/0
```

---

## Cost Estimates

**Monthly cost per environment (approximate):**
- RDS db.t3.micro: ~$13/month
- ElastiCache cache.t3.micro: ~$12/month
- **Total per environment**: ~$25/month
- **Both environments**: ~$50/month

---

## Deletion Commands (if needed)

**⚠️ WARNING: These commands will permanently delete resources and data!**

```bash
# Delete Beta Resources
aws rds delete-db-instance \
  --profile pedro-personal \
  --region us-east-1 \
  --db-instance-identifier whatsapp-ai-beta-db \
  --skip-final-snapshot

aws elasticache delete-cache-cluster \
  --profile pedro-personal \
  --region us-east-1 \
  --cache-cluster-id whatsapp-ai-beta-redis

# Delete Prod Resources
aws rds delete-db-instance \
  --profile pedro-personal \
  --region us-east-1 \
  --db-instance-identifier whatsapp-ai-prod-db \
  --skip-final-snapshot

aws elasticache delete-cache-cluster \
  --profile pedro-personal \
  --region us-east-1 \
  --cache-cluster-id whatsapp-ai-prod-redis
```

---

## Notes

1. **Network Configuration**: All database resources are VPC-internal only. RDS public accessibility has been disabled, and ElastiCache Redis is inherently private. EC2 instances connect via private IPs within the VPC.

2. **Security**:
   - RDS: Public accessibility **disabled** ✅
   - ElastiCache: Always VPC-internal (no public option) ✅
   - Security groups control EC2 → Database access
   - Legacy 0.0.0.0/0 rules remain but are ineffective for VPC-internal resources

3. **Backups**:
   - RDS: Automated backups enabled with 7-day retention
   - Redis: No automatic backups configured (increase SnapshotRetentionLimit if needed)

4. **Monitoring**: Enable CloudWatch alarms for:
   - CPU utilization
   - Memory usage
   - Connection counts
   - Storage space (RDS)
   - Network throughput

5. **Encryption**:
   - RDS: Storage encryption **enabled** ✅
   - Redis: At-rest and in-transit encryption **disabled** (can be enabled if needed)

6. **High Availability**: Both environments use single-AZ deployments. For production HA, consider:
   - RDS: Enable Multi-AZ for automatic failover
   - Redis: Use replication groups with multiple nodes across AZs

7. **Connection Testing from EC2**:
   ```bash
   # Test PostgreSQL connectivity
   psql -h whatsapp-ai-beta-db.cbas2uqkis4t.us-east-1.rds.amazonaws.com -U postgres -d whatsapp_chatbot

   # Test Redis connectivity
   redis-cli -h whatsapp-ai-beta-redis.nzvdck.0001.use1.cache.amazonaws.com -p 6379 ping
   ```
