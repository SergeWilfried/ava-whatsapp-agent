# CartaAI API Setup Guide

## Issue: Getting Mock Data Instead of API Data

If you're seeing mock data instead of real API data, it's likely because:

1. **No .env file exists** - Environment variables are not being loaded
2. **API is not enabled** - Feature flags are set to false
3. **Missing credentials** - API key, subdomain, or local_id not configured

---

## Quick Start: Enable CartaAI API

### Step 1: Create .env File

Copy the example file:
```bash
cp .env.example .env
```

### Step 2: Set Required Environment Variables

Edit `.env` and set these **REQUIRED** variables:

```bash
# Enable the API (CRITICAL!)
USE_CARTAAI_API="true"

# Enable menu API specifically
CARTAAI_MENU_ENABLED="true"

# Your API credentials (get from CartaAI dashboard)
CARTAAI_SUBDOMAIN="your-restaurant-subdomain"
CARTAAI_LOCAL_ID="your-local-id"
CARTAAI_API_KEY="your-api-key"

# Enable logging to debug API calls
ENABLE_API_LOGGING="true"
```

### Step 3: Restart Your Application

After editing .env, restart the application to load the new configuration:

```bash
# If running with python
python your_app.py

# If using docker
docker-compose restart

# If running as a service
systemctl restart your-service
```

---

## Environment Variables Reference

### Master Switch
- **`USE_CARTAAI_API`** (REQUIRED)
  - Set to `"true"` to enable API
  - Set to `"false"` to use mock data (default)
  - If this is false, ALL other settings are ignored

### API Credentials (Required if API enabled)
- **`CARTAAI_API_BASE_URL`**
  - Default: `https://ssgg.api.cartaai.pe/api/v1`
  - Only change if using a different CartaAI environment

- **`CARTAAI_SUBDOMAIN`** (REQUIRED)
  - Your restaurant's subdomain
  - Example: `"my-restaurant"`

- **`CARTAAI_LOCAL_ID`** (REQUIRED)
  - Your restaurant's local ID from CartaAI
  - Example: `"loc_12345"`

- **`CARTAAI_API_KEY`** (REQUIRED)
  - Your API authentication key
  - Get from CartaAI dashboard

### Feature Flags
- **`CARTAAI_MENU_ENABLED`**
  - Set to `"true"` to use API for menu data
  - Default: `"false"`

- **`CARTAAI_ORDERS_ENABLED`**
  - Set to `"true"` to use API for order creation
  - Default: `"false"`

- **`CARTAAI_DELIVERY_ENABLED`**
  - Set to `"true"` to use API for delivery tracking
  - Default: `"false"`

### Performance Settings
- **`CARTAAI_TIMEOUT`**
  - Request timeout in seconds
  - Default: `"30"`

- **`CARTAAI_MAX_RETRIES`**
  - Maximum retry attempts for failed requests
  - Default: `"3"`

- **`CARTAAI_RETRY_DELAY`**
  - Initial retry delay in seconds (exponential backoff)
  - Default: `"1.0"`

- **`CARTAAI_CACHE_TTL`**
  - Cache time-to-live in seconds
  - Default: `"900"` (15 minutes)

- **`CARTAAI_ENABLE_CACHE`**
  - Enable in-memory caching
  - Default: `"true"`

- **`CARTAAI_MAX_CONCURRENT_REQUESTS`**
  - Maximum parallel API requests
  - Default: `"10"`

### Logging
- **`ENABLE_API_LOGGING`**
  - Enable detailed API request/response logging
  - Set to `"true"` for debugging
  - Default: `"false"`

---

## Verification

### Check Configuration is Loaded

When the application starts with logging enabled, you should see:

```
============================================================
MenuAdapter initialization check:
  use_cartaai_api: True
  menu_api_enabled: True
  api_base_url: https://ssgg.api.cartaai.pe/api/v1
  subdomain: your-restaurant-subdomain
  local_id: your-local-id
  api_key: SET
  enable_api_logging: True
  enable_cache: True
============================================================
```

### Check API is Being Used

When the API is working correctly, you'll see logs like:

```
🔵 Using API to get menu structure
INFO - CartaAI API session created
INFO - API Request [0/3]: GET https://ssgg.api.cartaai.pe/api/v1/menu2/bot-structure
INFO - API Response: 200 | Time: 0.345s
```

### Check Mock Data is Being Used (Fallback)

If API is NOT configured or fails, you'll see:

```
🟡 Using MOCK data to get menu structure
  Reason: use_cartaai_api=False, menu_api_enabled=False, menu_service=NOT SET
```

---

## Troubleshooting

### Issue: Still getting mock data after setting env vars

**Solution:**
1. Verify .env file exists in project root
2. Restart the application (changes require restart)
3. Check logs for configuration values
4. Verify all REQUIRED variables are set

### Issue: No logs appearing

**Solution:**
1. Set `ENABLE_API_LOGGING="true"`
2. Restart application
3. Check logging configuration in your app

### Issue: API errors / Failed requests

**Solution:**
1. Verify credentials are correct (subdomain, local_id, api_key)
2. Check API base URL is correct
3. Verify network connectivity to CartaAI servers
4. Check CartaAI dashboard for API status
5. Review error logs for specific error messages

### Issue: Configuration validation fails

**Solution:**
The config validator checks:
- `subdomain` is set (not empty)
- `api_key` is set (not empty)

If validation fails, you'll see:
```
ERROR - Invalid CartaAI configuration, falling back to mock data
```

Make sure both values are set in your .env file.

---

## Example .env File (Minimum Required)

```bash
# Existing configuration...
# (keep your existing GROQ_API_KEY, WHATSAPP settings, etc.)

# CartaAI API - Minimum required to enable API
USE_CARTAAI_API="true"
CARTAAI_MENU_ENABLED="true"
CARTAAI_SUBDOMAIN="my-restaurant"
CARTAAI_LOCAL_ID="loc_12345"
CARTAAI_API_KEY="your-secret-api-key"
ENABLE_API_LOGGING="true"
```

---

## Example .env File (Full Configuration)

```bash
# CartaAI API Configuration
USE_CARTAAI_API="true"

# API Credentials
CARTAAI_API_BASE_URL="https://ssgg.api.cartaai.pe/api/v1"
CARTAAI_SUBDOMAIN="my-restaurant"
CARTAAI_LOCAL_ID="loc_12345"
CARTAAI_API_KEY="your-secret-api-key"

# Feature Flags
CARTAAI_MENU_ENABLED="true"
CARTAAI_ORDERS_ENABLED="true"
CARTAAI_DELIVERY_ENABLED="false"

# Performance Settings
CARTAAI_TIMEOUT="30"
CARTAAI_MAX_RETRIES="3"
CARTAAI_RETRY_DELAY="1.0"
CARTAAI_CACHE_TTL="900"
CARTAAI_ENABLE_CACHE="true"
CARTAAI_MAX_CONCURRENT_REQUESTS="10"

# Logging
ENABLE_API_LOGGING="true"
```

---

## Summary of Fixes Applied

### 1. Fixed Empty Environment Variable Bug
**File:** `src/ai_companion/core/config.py` (line 63)

**Before (BUG):**
```python
use_cartaai_api=os.getenv("", "false").lower() == "true",
```

**After (FIXED):**
```python
use_cartaai_api=os.getenv("USE_CARTAAI_API", "false").lower() == "true",
```

### 2. Fixed Missing Logging Parameter
**File:** `src/ai_companion/services/cartaai/__init__.py` (lines 36-38)

**Added:**
```python
retry_delay=config.retry_delay,
max_concurrent_requests=config.max_concurrent_requests,
enable_logging=config.enable_api_logging,  # This was missing!
```

### 3. Added Debug Logging
**Files:**
- `src/ai_companion/services/menu_adapter.py`

Added logs to show:
- Configuration values on initialization
- Which code path is taken (API vs mock)
- Reason for using mock data (if applicable)

---

## Next Steps

1. Create your `.env` file from `.env.example`
2. Set the required CartaAI environment variables
3. Restart your application
4. Check logs to verify API is being used
5. Test menu browsing to confirm API data is loaded

---

**Date:** 2024-12-04
