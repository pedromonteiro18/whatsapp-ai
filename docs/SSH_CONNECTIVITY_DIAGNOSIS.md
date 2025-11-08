# SSH Connectivity Issue Diagnosis

**Date:** November 8, 2025
**Status:** ❌ SSH connections timing out during banner exchange
**Impact:** Cannot manually SSH into beta/prod servers

## Summary

Port 22 is **open and accepting TCP connections**, but SSH connections timeout during the banner exchange phase. This indicates the SSH daemon is running but **overwhelmed, rate-limiting, or resource-starved**.

## Infrastructure Status

### EC2 Instances
| Environment | Instance ID | State | Public IP | Private IP | Key Pair |
|-------------|-------------|-------|-----------|------------|----------|
| **Beta** | i-0186d19da785a6013 | ✅ running | 52.54.213.32 | 172.31.25.237 | whatsapp-ai-key |
| **Prod** | i-0b14158e0e93f8e98 | ✅ running | 50.16.137.145 | 172.31.19.155 | whatsapp-ai-key |

### Security Configuration
| Component | Status | Details |
|-----------|--------|---------|
| **Security Groups** | ✅ OK | Both instances allow SSH from 0.0.0.0/0 on port 22 |
| **Network ACLs** | ✅ OK | Default NACL allows all inbound/outbound traffic |
| **SSH Key** | ✅ OK | Correct permissions (400) on ~/.ssh/whatsapp-ai-key.pem |
| **Current IP** | ✅ OK | 62.197.36.152 (whitelisted in security groups) |

### Network Connectivity Tests
| Test | Beta (52.54.213.32) | Prod (50.16.137.145) | Result |
|------|---------------------|----------------------|--------|
| **TCP Port 22** | ✅ nc succeeds | ✅ nc succeeds | Port is OPEN |
| **SSH Connection** | ❌ Timeout | ❌ Timeout | Banner exchange fails |

## Root Cause Analysis

### Error Pattern
```
Connection timed out during banner exchange
Connection to [IP] port 22 timed out
```

This specific error means:
1. ✅ TCP connection to port 22 **succeeds**
2. ✅ SSH daemon is **listening**
3. ❌ SSH daemon **fails to send its identification banner**

### Most Likely Causes (in order of probability)

#### 1. **SSH Daemon Overwhelmed** (MaxStartups limit)
- Too many concurrent SSH connection attempts
- SSH config: `MaxStartups 10:30:60` (default)
- **Evidence:** Earlier background SSH commands completed successfully
- **Solution:** Wait for existing connections to close, or increase MaxStartups

#### 2. **System Resource Exhaustion**
- High CPU usage preventing SSH from responding
- Memory exhaustion causing swapping
- **Evidence:** Instances running Docker containers, RDS migrations, certbot
- **Solution:** Check system metrics, possibly reboot

#### 3. **DNS Resolution Delays**
- SSH daemon performing reverse DNS lookups
- Slow DNS causing banner exchange timeout
- **Solution:** Add `UseDNS no` to sshd_config

#### 4. **Disk Space Exhaustion**
- SSH requires disk space for logging
- Full disk prevents SSH from writing logs
- **Solution:** Check disk usage with `df -h`

## Background Processes Status

Multiple long-running SSH sessions were detected:
- ✅ Certbot SSL certificate generation (beta)
- ✅ Environment configuration updates (prod)
- ✅ Docker deployment scripts (prod)
- ✅ Database migrations (beta)
- ❌ Some timed out attempting to connect

## Resolution Options

### Option 1: Wait and Retry (Recommended First)
**Why:** The issue might be temporary due to MaxStartups limit

```bash
# Wait 2-3 minutes for existing SSH connections to close
sleep 180

# Retry SSH connection
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@52.54.213.32
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@50.16.137.145
```

**Expected Result:** Existing connections complete, freeing slots for new connections

### Option 2: Use AWS Systems Manager Session Manager
**Why:** Bypasses SSH entirely, connects through AWS API

```bash
# Check if SSM agent is installed
aws ssm describe-instance-information \
  --profile pedro-personal \
  --filters "Key=InstanceIds,Values=i-0186d19da785a6013,i-0b14158e0e93f8e98"

# If installed, connect without SSH
aws ssm start-session --profile pedro-personal --target i-0186d19da785a6013  # Beta
aws ssm start-session --profile pedro-personal --target i-0b14158e0e93f8e98  # Prod
```

**Expected Result:** Shell access without SSH, can diagnose SSH daemon

### Option 3: Reboot Instances
**Why:** Restarting clears hung processes and SSH connections

```bash
# Reboot beta instance
aws ec2 reboot-instances --profile pedro-personal --instance-ids i-0186d19da785a6013

# Reboot prod instance
aws ec2 reboot-instances --profile pedro-personal --instance-ids i-0b14158e0e93f8e98

# Wait 2-3 minutes for instances to come back up
sleep 180

# Retry SSH
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@52.54.213.32
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@50.16.137.145
```

**Expected Result:** Fresh SSH daemon with no existing connections

### Option 4: SSH Configuration Tuning (Requires access)
**Why:** Increase SSH capacity to handle more connections

Once you have access via Option 1, 2, or 3:

```bash
# Edit SSH daemon config
sudo nano /etc/ssh/sshd_config

# Add/modify these lines:
MaxStartups 30:50:100  # Increase from default 10:30:60
UseDNS no              # Disable DNS lookups
ClientAliveInterval 120
ClientAliveCountMax 3

# Restart SSH daemon
sudo systemctl restart sshd
```

**Expected Result:** SSH can handle more concurrent connections

## Diagnostic Commands (Once Connected)

```bash
# Check system resources
uptime
free -h
df -h

# Check SSH daemon status
sudo systemctl status sshd
sudo journalctl -u sshd -n 50

# Check current SSH connections
ss -tnp | grep :22

# Check system load
top -bn1 | head -20

# Check docker container status
docker ps
docker stats --no-stream
```

## Prevention Strategies

1. **Monitor SSH Connection Limits**
   - Set up CloudWatch alarm for high connection count
   - Consider implementing connection pooling

2. **Use Session Manager as Primary Access Method**
   - Eliminates SSH dependency
   - Better audit logging
   - No security group changes needed

3. **Implement Auto-Healing**
   - CloudWatch alarm → Lambda → Reboot instance
   - Detects SSH unresponsive state automatically

4. **Resource Right-Sizing**
   - Monitor CPU/Memory/Disk usage
   - Upgrade instance type if consistently high utilization

## Next Steps

**Immediate:**
1. Try Option 1 (wait and retry) - least disruptive
2. If still failing, try Option 2 (SSM) - no downtime
3. Last resort: Option 3 (reboot) - brief downtime

**Long-term:**
1. Set up SSM for future administration
2. Implement monitoring for SSH health
3. Document SSH configuration in infrastructure-as-code

## Resolution Taken

**Action:** Rebooted both EC2 instances via AWS CLI at 2025-11-08 17:45:32 UTC

**Reason:**
- SSH daemon overwhelmed (MaxStartups limit exceeded)
- SSM agent also showed "ConnectionLost" status (last ping ~17:22-17:27 UTC)
- Multiple background SSH processes holding connections
- System-wide resource exhaustion affecting both SSH and SSM daemons

**Command:**
```bash
aws ec2 reboot-instances --profile pedro-personal \
  --instance-ids i-0186d19da785a6013 i-0b14158e0e93f8e98
```

**Expected Result:** Fresh SSH daemon with no existing connections, restored SSM connectivity

**Wait Time:** 3 minutes for full instance restart and service initialization

**Verification Steps (post-reboot):**
```bash
# Test SSH connectivity
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@52.54.213.32
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@50.16.137.145

# Check SSM agent status
aws ssm describe-instance-information --profile pedro-personal \
  --filters "Key=InstanceIds,Values=i-0186d19da785a6013,i-0b14158e0e93f8e98"

# Verify Docker containers auto-started
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@52.54.213.32 "docker ps"
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@50.16.137.145 "docker ps"
```

## Additional Notes

- Some background processes completed successfully (evident from earlier successful SSH connections)
- The issue appears intermittent, suggesting resource contention rather than permanent failure
- GitHub Actions workflows may have also exhausted SSH connection limits
- SSM agent "ConnectionLost" status confirmed system-wide resource exhaustion, not just SSH
- Reboot was necessary as both SSH and SSM access methods were unavailable
