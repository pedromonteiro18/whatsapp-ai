#!/bin/bash
# Start beta EC2 instance
# Usage: ./scripts/start-beta.sh

set -e

# Configuration (replace with your actual instance ID)
INSTANCE_ID="${BETA_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "Starting beta EC2 instance..."
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"

# Start the instance
aws ec2 start-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

echo "Waiting for instance to be running..."
aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

# Get the public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "================================"
echo "Beta instance started successfully!"
echo "Public IP: $PUBLIC_IP"
echo "================================"
echo ""
echo "You can now SSH with:"
echo "  ssh ubuntu@$PUBLIC_IP"
echo ""
echo "Or access the beta site at:"
echo "  https://beta.yourdomain.com"
