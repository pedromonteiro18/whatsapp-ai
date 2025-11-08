#!/bin/bash
# Start production EC2 instance
# Usage: ./scripts/start-prod.sh

set -e

# Configuration (replace with your actual instance ID)
INSTANCE_ID="${PROD_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "Starting production EC2 instance..."
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

# Get the public IP (or use Elastic IP if configured)
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "================================"
echo "Production instance started successfully!"
echo "Public IP: $PUBLIC_IP"
echo "================================"
echo ""
echo "You can now SSH with:"
echo "  ssh ubuntu@$PUBLIC_IP"
echo ""
echo "Or access the production site at:"
echo "  https://yourdomain.com"
