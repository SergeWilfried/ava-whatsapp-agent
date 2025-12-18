# Webhook Error Handling Fix

## Problem
According to Meta's WhatsApp Cloud API documentation:
> If we send a webhook request to your endpoint and your server responds with an HTTP status code other than 200, or if we are unable to deliver the webhook for another reason, we will keep trying with decreasing frequency until the request succeeds, for up to 7 days.

The previous implementation was returning various error status codes (400, 404, 500) when encountering errors, causing Meta to retry webhooks indefinitely for up to 7 days.

## Solution
Updated the webhook handler to **always return HTTP 200 OK** for POST requests (webhook events), while logging all errors internally. This prevents Meta from retrying failed webhooks.

## Changes Made

### File: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`

#### 1. Missing phone_number_id (Line 79-82)
**Before:**
```python
if not phone_number_id:
    logger.error("No phone_number_id found in webhook metadata")
    return Response(content="Missing phone_number_id in webhook", status_code=400)
```

**After:**
```python
if not phone_number_id:
    logger.error("No phone_number_id found in webhook metadata")
    # Return 200 to prevent Meta from retrying
    return Response(content="OK", status_code=200)
```

#### 2. Business not found (Line 95-98)
**Before:**
```python
if not business:
    logger.error(f"No business found for phone_number_id: {phone_number_id}")
    return Response(content="Business not found for this phone number", status_code=404)
```

**After:**
```python
if not business:
    logger.error(f"No business found for phone_number_id: {phone_number_id}")
    # Return 200 to prevent Meta from retrying
    return Response(content="OK", status_code=200)
```

#### 3. Invalid business credentials (Line 105-108)
**Before:**
```python
if not whatsapp_token:
    logger.error(f"No valid WhatsApp token for business: {business_name}")
    return Response(content="Invalid business credentials", status_code=500)
```

**After:**
```python
if not whatsapp_token:
    logger.error(f"No valid WhatsApp token for business: {business_name}")
    # Return 200 to prevent Meta from retrying
    return Response(content="OK", status_code=200)
```

#### 4. Failed to send message (Line 915-920)
**Before:**
```python
if not success:
    return Response(content="Failed to send message", status_code=500)

return Response(content="Message processed", status_code=200)
```

**After:**
```python
if not success:
    logger.error("Failed to send message to user")
    # Return 200 to prevent Meta from retrying
    return Response(content="OK", status_code=200)

return Response(content="OK", status_code=200)
```

#### 5. Unknown event type (Line 925-928)
**Before:**
```python
else:
    return Response(content="Unknown event type", status_code=400)
```

**After:**
```python
else:
    logger.warning(f"Unknown event type received: {change_value.keys()}")
    # Return 200 to prevent Meta from retrying
    return Response(content="OK", status_code=200)
```

#### 6. Global exception handler (Line 930-934)
**Before:**
```python
except Exception as e:
    logger.error(f"Error processing message: {e}", exc_info=True)
    return Response(content="Internal server error", status_code=500)
```

**After:**
```python
except Exception as e:
    logger.error(f"Error processing message: {e}", exc_info=True)
    # CRITICAL: Always return 200 to prevent Meta from retrying for 7 days
    # Log the error but acknowledge receipt of the webhook
    return Response(content="OK", status_code=200)
```

## What Was NOT Changed

### Webhook Verification (GET request)
The webhook verification endpoint still returns 403 on verification token mismatch. This is correct because:
- It only happens during GET requests (setup/verification)
- It's not a webhook event delivery
- The 403 helps developers identify configuration issues during setup

```python
if request.method == "GET":
    params = request.query_params
    if params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(content="Verification token mismatch", status_code=403)  # ✓ Correct
```

## Benefits

1. **No infinite retries**: Meta will not retry failed webhooks for 7 days
2. **Better error tracking**: All errors are logged with full stack traces
3. **Prevents webhook queue buildup**: Failed webhooks are acknowledged and won't clog the system
4. **Follows Meta's best practices**: Aligns with WhatsApp Cloud API recommendations

## Monitoring

All errors are still logged with full context:
- `logger.error()` for critical issues (missing credentials, failed sends)
- `logger.warning()` for non-critical issues (unknown event types)
- Full exception info with `exc_info=True`

Monitor your logs to identify and fix recurring issues without relying on webhook retries.

## Testing

To verify the fix:
1. Send a test webhook with invalid data
2. Check logs for error messages
3. Verify webhook returns HTTP 200 OK
4. Confirm Meta does not retry the webhook

## References

- [Meta WhatsApp Cloud API - Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- Meta's recommendation: Return 200 for all webhook requests, handle errors internally
