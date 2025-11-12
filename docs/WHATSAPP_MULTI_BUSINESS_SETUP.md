# WhatsApp Multi-Business Setup Guide

This guide explains how to set up and use the multi-business WhatsApp webhook system that automatically routes messages to the correct business based on the phone number ID from incoming webhooks.

## Overview

The system now supports multiple businesses with different WhatsApp Business accounts. When a webhook message arrives:

1. **Extracts the phone number ID** from the webhook metadata
2. **Looks up the business** in MongoDB by matching the phone number ID
3. **Retrieves and decrypts** the business-specific WhatsApp access token
4. **Routes the conversation** using business-specific credentials
5. **Maintains separate sessions** per business using `subdomain:phone_number` as session ID

## Architecture

```
WhatsApp Cloud API Webhook
         ↓
    Extract phone_number_id from metadata
         ↓
    Query MongoDB for business with matching whatsappPhoneNumberIds
         ↓
    Decrypt business WhatsApp access token
         ↓
    Process message through AI Companion
         ↓
    Send response using business-specific credentials
```

## Setup Instructions

### 1. Environment Variables

Update your `.env` file with the following variables:

```bash
# MongoDB Configuration (Required for multi-business)
MONGODB_URI="mongodb://localhost:27017/your-database"
MONGODB_DB_NAME="your_database_name"
ENCRYPTION_SECRET="your-32-character-secret-key"

# Fallback WhatsApp Credentials (Optional - used if business lookup fails)
WHATSAPP_PHONE_NUMBER_ID="your-fallback-phone-id"
WHATSAPP_TOKEN="your-fallback-token"
WHATSAPP_VERIFY_TOKEN="your-webhook-verify-token"

# Other required environment variables
GROQ_API_KEY="your-groq-api-key"
ELEVENLABS_API_KEY="your-elevenlabs-key"
```

### 2. Install Dependencies

Install the new MongoDB and encryption dependencies:

```bash
# Using uv (recommended)
uv pip install motor pymongo cryptography

# Or using pip
pip install motor>=3.3.0 pymongo>=4.6.0 cryptography>=41.0.0
```

### 3. MongoDB Business Schema

Ensure your MongoDB `businesses` collection has the following fields:

```javascript
{
  "_id": ObjectId("..."),
  "name": "My Business",
  "subDomain": "mybusiness",
  "wabaId": "123456789012345",
  "whatsappPhoneNumberIds": ["987654321098765"],  // Array of phone number IDs
  "whatsappAccessToken": "encrypted_token_here",   // Encrypted access token
  "whatsappRefreshToken": "encrypted_refresh_here", // Optional
  "whatsappTokenExpiresAt": ISODate("2025-12-31T23:59:59Z"),
  "whatsappEnabled": true,
  "isActive": true
}
```

### 4. Encryption Setup

The `ENCRYPTION_SECRET` must match the secret used in your Node.js backend for encrypting/decrypting tokens.

**Important:** The encryption implementation uses:
- **Algorithm:** Fernet (symmetric encryption)
- **Key Derivation:** SHA-256 hash of `ENCRYPTION_SECRET`, base64-encoded
- **Storage Format:** Hex-encoded encrypted bytes in MongoDB

## How It Works

### Webhook Message Structure

WhatsApp sends webhook messages with this structure:

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "metadata": {
              "phone_number_id": "987654321098765"  // This identifies the business
            },
            "messages": [
              {
                "from": "15551234567",
                "type": "text",
                "text": {
                  "body": "Hello!"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Business Lookup Flow

1. **Extract phone_number_id:**
   ```python
   phone_number_id = change_value.get("metadata", {}).get("phone_number_id")
   ```

2. **Query MongoDB:**
   ```python
   business = await business_service.get_business_by_phone_number_id(phone_number_id)
   ```

3. **Decrypt credentials:**
   ```python
   whatsapp_token = business.get("decryptedAccessToken")
   ```

4. **Create session ID:**
   ```python
   session_id = f"{business_subdomain}:{from_number}"
   ```

### Session Management

Sessions are now scoped by business to prevent cross-contamination:

- **Old format:** `15551234567` (just the phone number)
- **New format:** `mybusiness:15551234567` (subdomain:phone_number)

This ensures that:
- Each business has isolated conversation history
- The same customer number can interact with different businesses independently
- Memory and context are business-specific

## API Reference

### BusinessService

Located in: `src/ai_companion/services/business_service.py`

#### Methods

**`get_business_by_phone_number_id(phone_number_id: str)`**

Finds a business by WhatsApp phone number ID.

```python
business_service = get_business_service()
business = await business_service.get_business_by_phone_number_id("987654321098765")

if business:
    print(f"Business: {business['name']}")
    print(f"Token: {business['decryptedAccessToken']}")
```

**`get_business_by_subdomain(subdomain: str)`**

Finds a business by subdomain.

```python
business = await business_service.get_business_by_subdomain("mybusiness")
```

**`list_businesses_with_whatsapp()`**

Lists all active businesses with WhatsApp enabled.

```python
businesses = await business_service.list_businesses_with_whatsapp()
for business in businesses:
    print(f"- {business['name']}: {business['subDomain']}")
```

**`decrypt_token(encrypted_token: str)`**

Decrypts a WhatsApp access token.

```python
token = business_service.decrypt_token(encrypted_hex_string)
```

## Testing

### 1. Extract Credentials Script

Use the provided script to verify your MongoDB setup:

```bash
# Extract all businesses with WhatsApp
npx ts-node scripts/extractWhatsAppCredentials.ts

# Extract specific business
npx ts-node scripts/extractWhatsAppCredentials.ts mybusiness
```

### 2. Test Webhook Locally

1. Start the FastAPI server:
   ```bash
   python -m uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint:app --reload
   ```

2. Use ngrok to expose your local server:
   ```bash
   ngrok http 8000
   ```

3. Update your WhatsApp webhook URL in Meta Developer Console:
   ```
   https://your-ngrok-url.ngrok.io/whatsapp_response
   ```

4. Send a test message to your WhatsApp Business number

### 3. Monitor Logs

The system logs detailed information:

```python
# Business lookup
logger.info(f"Processing message for business: {business_name} (subdomain: {business_subdomain})")

# Message sending
logger.debug(f"Sending message to {from_number} via phone number ID: {phone_id}")

# Errors
logger.error(f"No business found for phone_number_id: {phone_number_id}")
```

## Troubleshooting

### Business Not Found

**Error:** `No business found for phone_number_id: xxx`

**Solutions:**
1. Verify the phone number ID exists in `whatsappPhoneNumberIds` array
2. Check that `whatsappEnabled: true` and `isActive: true`
3. Run the extraction script to verify database state

### Token Decryption Failed

**Error:** `Failed to decrypt WhatsApp access token`

**Solutions:**
1. Verify `ENCRYPTION_SECRET` matches your Node.js backend
2. Check that tokens are stored as hex-encoded encrypted strings
3. Ensure `cryptography` package is installed

### Invalid Credentials

**Error:** `Invalid business credentials`

**Solutions:**
1. Check that `whatsappAccessToken` is not null/empty
2. Verify token hasn't expired (`whatsappTokenExpiresAt`)
3. Test token manually with WhatsApp API

### Webhook Verification Fails

**Error:** `Verification token mismatch`

**Solutions:**
1. Ensure `WHATSAPP_VERIFY_TOKEN` matches Meta Developer Console
2. Check webhook URL is correct
3. Verify GET request handling works

## Security Best Practices

1. **Never log decrypted tokens** - Only log first 20 characters for debugging
2. **Rotate encryption secrets** regularly
3. **Use HTTPS** for webhook endpoints in production
4. **Implement rate limiting** on webhook endpoint
5. **Validate webhook signatures** (future enhancement)
6. **Monitor failed decryption attempts**

## Migration Guide

### From Single-Business to Multi-Business

1. **Backup your `.env` file** with existing credentials
2. **Add MongoDB configuration** to `.env`
3. **Install new dependencies**
4. **Keep fallback credentials** for backward compatibility
5. **Test with one business first** before adding more
6. **Monitor logs** during initial deployment

The system maintains backward compatibility by falling back to environment variable credentials if MongoDB lookup fails.

## Future Enhancements

- [ ] Webhook signature validation for security
- [ ] Token refresh automation when tokens expire
- [ ] Business-specific AI personality/settings
- [ ] Analytics and message tracking per business
- [ ] Rate limiting per business
- [ ] Multi-language support per business
- [ ] Custom prompts/instructions per business

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify MongoDB connection and credentials
3. Test business lookup independently
4. Review the WhatsApp Cloud API documentation
5. Check Meta Business Suite for account status
