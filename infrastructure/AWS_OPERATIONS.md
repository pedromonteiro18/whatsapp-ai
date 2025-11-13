# AWS Operations Guide

Quick reference for managing AWS resources for the WhatsApp AI project.

---

## Beta Environment Status

### Currently Stopped Resources (as of 2025-11-11)
- ✅ **EC2**: `whatsapp-ai-beta` (i-0186d19da785a6013) - **STOPPED**
- ✅ **RDS**: `whatsapp-ai-beta-db` - **STOPPED**
- ⚠️ **ElastiCache Redis**: `whatsapp-ai-beta-redis` - **RUNNING** (cannot be stopped, only deleted)

---

## Start/Stop Commands

### EC2 Instances

**Stop Beta:**
```bash
aws ec2 stop-instances --profile pedro-personal --region us-east-1 --instance-ids i-0186d19da785a6013
```

**Start Beta:**
```bash
aws ec2 start-instances --profile pedro-personal --region us-east-1 --instance-ids i-0186d19da785a6013
```

**Stop Production:**
```bash
aws ec2 stop-instances --profile pedro-personal --region us-east-1 --instance-ids i-0b14158e0e93f8e98
```

**Start Production:**
```bash
aws ec2 start-instances --profile pedro-personal --region us-east-1 --instance-ids i-0b14158e0e93f8e98
```

### RDS Database

**Stop Beta RDS:**
```bash
aws rds stop-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-beta-db
```

**Start Beta RDS:**
```bash
aws rds start-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-beta-db
```

**Stop Production RDS:**
```bash
aws rds stop-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-prod-db
```

**Start Production RDS:**
```bash
aws rds start-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-prod-db
```

**Note:** RDS can only be stopped for 7 days. After 7 days, AWS automatically starts it.

### ElastiCache (Redis)

**⚠️ ElastiCache cannot be stopped - only deleted or kept running.**

**Delete Beta Redis (saves costs but loses all data):**
```bash
aws elasticache delete-cache-cluster --profile pedro-personal --region us-east-1 --cache-cluster-id whatsapp-ai-beta-redis
```

**Create snapshot before deleting (to preserve data):**
```bash
aws elasticache create-snapshot --profile pedro-personal --region us-east-1 \
  --cache-cluster-id whatsapp-ai-beta-redis \
  --snapshot-name whatsapp-ai-beta-redis-backup-$(date +%Y%m%d)
```

---

## Check Resource Status

**List all EC2 instances:**
```bash
aws ec2 describe-instances --profile pedro-personal --region us-east-1 \
  --query "Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key=='Name'].Value|[0]]" \
  --output table
```

**List all RDS instances:**
```bash
aws rds describe-db-instances --profile pedro-personal --region us-east-1 \
  --query "DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Engine]" \
  --output table
```

**List all ElastiCache clusters:**
```bash
aws elasticache describe-cache-clusters --profile pedro-personal --region us-east-1 \
  --query "CacheClusters[*].[CacheClusterId,CacheClusterStatus,Engine]" \
  --output table
```

---

## Cost Optimization Tips

### When to Stop Resources

**Beta Environment (Development/Testing):**
- ✅ Stop EC2 when not actively developing
- ✅ Stop RDS overnight or on weekends
- ⚠️ ElastiCache: Consider deleting if not needed daily

**Production Environment:**
- ❌ Never stop unless maintenance required
- ✅ Use reserved instances for cost savings
- ✅ Monitor usage and right-size instances

### Estimated Costs When Running

| Resource | Type | Monthly Cost (Approx) |
|----------|------|-----------------------|
| EC2 Beta | t2.micro | ~$8.50 |
| EC2 Prod | t2.micro | ~$8.50 |
| RDS Beta | db.t3.micro | ~$15 |
| RDS Prod | db.t3.micro | ~$15 |
| ElastiCache Beta | cache.t3.micro | ~$12 |
| ElastiCache Prod | cache.t3.micro | ~$12 |
| **Total Running** | | **~$71/month** |

**Cost when stopped:**
- EC2 stopped: $0 (EBS storage still charged ~$1/month per 10GB)
- RDS stopped: $0 (storage still charged)
- ElastiCache: Must delete to stop charges

---

## Important Notes

1. **RDS Auto-Start**: Stopped RDS instances automatically start after 7 days
2. **ElastiCache**: Cannot be stopped - must delete to save costs
3. **Data Loss**: Stopping EC2/RDS is safe. Deleting ElastiCache loses all cached data
4. **IP Addresses**: EC2 public IPs change when stopped/started (use Elastic IP or DuckDNS)
5. **Startup Time**: EC2 ~30 seconds, RDS ~5 minutes to fully start

---

## Quick Actions

**Stop entire beta environment (except Redis):**
```bash
# Stop EC2
aws ec2 stop-instances --profile pedro-personal --region us-east-1 --instance-ids i-0186d19da785a6013

# Stop RDS
aws rds stop-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-beta-db
```

**Start entire beta environment:**
```bash
# Start EC2
aws ec2 start-instances --profile pedro-personal --region us-east-1 --instance-ids i-0186d19da785a6013

# Start RDS
aws rds start-db-instance --profile pedro-personal --region us-east-1 --db-instance-identifier whatsapp-ai-beta-db

# Wait for services to start (takes ~5 minutes)
watch -n 10 'aws ec2 describe-instances --profile pedro-personal --region us-east-1 --instance-ids i-0186d19da785a6013 --query "Reservations[0].Instances[0].State.Name"'
```

---

**Last Updated**: 2025-11-11
**Last Stopped**: Beta environment (EC2 + RDS)
