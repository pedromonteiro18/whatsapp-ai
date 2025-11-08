#!/bin/bash
# Stop production EC2 instance
# Usage: ./scripts/stop-prod.sh

set -e

# Configuration (replace with your actual instance ID)
INSTANCE_ID="${PROD_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "WARNING: You are about to stop the PRODUCTION instance!"
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Stopping production EC2 instance..."

# Stop the instance
aws ec2 stop-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

echo "Waiting for instance to be stopped..."
aws ec2 wait instance-stopped \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

echo "================================"
echo "Production instance stopped successfully!"
echo "================================"
echo ""
echo "Note: Your data is preserved in EBS volumes."
echo "You will only be charged for storage (~\$1/month) while stopped."
echo ""
echo "WARNING: Your production site is now offline!"
