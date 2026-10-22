#!/bin/bash
set -euo pipefail

# Certbot entrypoint script for automated Let's Encrypt certificate management
# This script runs inside the certbot container to obtain/renew certificates

echo "Certbot entrypoint starting..."

# Set environment variables from secrets
SSL_EMAIL="${SSL_EMAIL:-admin@nebula.example.com}"
SSL_DOMAINS="${SSL_DOMAINS:-nebula.example.com}"

if [ -z "$SSL_DOMAINS" ]; then
    echo "ERROR: SSL_DOMAINS environment variable is required"
    exit 1
fi

# Function to obtain or renew certificate
obtain_cert() {
    echo "Attempting to obtain/renew certificate for: $SSL_DOMAINS"
    
    certbot certonly --webroot \
        --webroot-path /var/www/certbot \
        --email "$SSL_EMAIL" \
        --agree-tos \
        --no-eff-email \
        --expand \
        --domain "$SSL_DOMAINS" \
        --deploy-hook "/deploy-cert.sh" \
        --non-interactive \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo "Certificate obtained/renewed successfully"
        return 0
    else
        echo "Certificate operation failed (may need manual intervention)"
        return 1
    fi
}

# Function to check certificate expiration
check_cert() {
    echo "Checking certificate expiration..."
    
    for domain in $(echo "$SSL_DOMAINS" | tr ',' ' '); do
        cert_path="/etc/letsencrypt/live/$domain/fullchain.pem"
        if [ -f "$cert_path" ]; then
            expires_in=$(openssl x509 -checkend 2592000 -noout -in "$cert_path" 2>&1)
            if [ $? -eq 0 ]; then
                echo "Certificate for $domain is valid (expires in > 30 days)"
            else
                echo "Certificate for $domain expires within 30 days - will renew"
                return 1
            fi
        else
            echo "No certificate found for $domain - will obtain"
            return 1
        fi
    done
    
    return 0
}

# Main logic
if check_cert; then
    echo "All certificates are valid - no action needed"
    echo "Certbot entrypoint completed successfully"
    exit 0
else
    echo "Certificate renewal needed"
    obtain_cert
    exit $?
fi
