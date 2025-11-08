#!/bin/bash
# Stop beta EC2 instance
# Usage: ./scripts/stop-beta.sh

set -e

# Configuration (replace with your actual instance ID)
INSTANCE_ID="${BETA_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "Stopping beta EC2 instance..."
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"

# Stop the instance
aws ec2 stop-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

echo "Waiting for instance to be stopped..."
aws ec2 wait instance-stopped \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

echo "================================"
echo "Beta instance stopped successfully!"
echo "================================"
echo ""
echo "Note: Your data is preserved in EBS volumes."
echo "You will only be charged for storage (~\$1/month) while stopped."
