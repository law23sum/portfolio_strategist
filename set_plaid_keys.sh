#!/bin/bash
# Helper script to set Plaid keys in .env file

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

echo "Setting Plaid keys in .env file..."
echo ""
echo "Please enter your Plaid credentials:"
echo ""

read -p "Plaid Client ID: " CLIENT_ID
read -p "Plaid Secret: " SECRET
read -p "Plaid Environment (sandbox/development/production) [sandbox]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-sandbox}

read -p "Plaid Webhook URL (optional, press Enter to skip): " WEBHOOK_URL

# Update or add PLAID_CLIENT_ID
if grep -q "^PLAID_CLIENT_ID=" "$ENV_FILE"; then
    sed -i.bak "s|^PLAID_CLIENT_ID=.*|PLAID_CLIENT_ID=$CLIENT_ID|" "$ENV_FILE"
else
    echo "PLAID_CLIENT_ID=$CLIENT_ID" >> "$ENV_FILE"
fi

# Update or add PLAID_SECRET
if grep -q "^PLAID_SECRET=" "$ENV_FILE"; then
    sed -i.bak "s|^PLAID_SECRET=.*|PLAID_SECRET=$SECRET|" "$ENV_FILE"
else
    echo "PLAID_SECRET=$SECRET" >> "$ENV_FILE"
fi

# Update or add PLAID_ENVIRONMENT
if grep -q "^PLAID_ENVIRONMENT=" "$ENV_FILE"; then
    sed -i.bak "s|^PLAID_ENVIRONMENT=.*|PLAID_ENVIRONMENT=$ENVIRONMENT|" "$ENV_FILE"
else
    echo "PLAID_ENVIRONMENT=$ENVIRONMENT" >> "$ENV_FILE"
fi

# Update or add PLAID_WEBHOOK_URL
if [ -n "$WEBHOOK_URL" ]; then
    if grep -q "^PLAID_WEBHOOK_URL=" "$ENV_FILE"; then
        sed -i.bak "s|^PLAID_WEBHOOK_URL=.*|PLAID_WEBHOOK_URL=$WEBHOOK_URL|" "$ENV_FILE"
    else
        echo "PLAID_WEBHOOK_URL=$WEBHOOK_URL" >> "$ENV_FILE"
    fi
fi

# Clean up backup file
rm -f "$ENV_FILE.bak"

echo ""
echo "✓ Plaid keys updated in .env file!"
echo ""
echo "Next steps:"
echo "1. Restart your Docker containers: docker compose restart web"
echo "2. Run bootstrap command: docker compose exec web python manage.py bootstrap_plaid"

