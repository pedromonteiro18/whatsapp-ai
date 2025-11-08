# Deployment Server IPs

## Environment IPs

- **Beta**: `52.54.213.32` - https://resort-booking-beta.duckdns.org
- **Production**: `50.16.137.145` - https://resort-booking.duckdns.org

## SSH Access

```bash
# Beta
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@52.54.213.32

# Production
ssh -i ~/.ssh/whatsapp-ai-key.pem ubuntu@50.16.137.145
```

## GitHub Secrets

The following GitHub Secrets are configured for CI/CD:

- `BETA_HOST`: 52.54.213.32
- `BETA_SSH_USER`: ubuntu
- `BETA_SSH_KEY`: SSH private key for beta server

- `PROD_HOST`: 50.16.137.145
- `PROD_SSH_USER`: ubuntu
- `PROD_SSH_KEY`: SSH private key for production server
