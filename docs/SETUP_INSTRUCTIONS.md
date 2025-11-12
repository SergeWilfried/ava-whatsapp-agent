# ⚡ Quick Setup Instructions - Optimized Version

## Current Status: ✅ Dependencies Installed

You've successfully installed all dependencies. Here's what you need to do next:

---

## Step 1: Configure MongoDB Credentials

Edit your `.env` file and fill in these values:

```bash
# MongoDB Configuration (REQUIRED)
MONGODB_URI="mongodb://localhost:27017/your-database"  # Your MongoDB connection string
MONGODB_DB_NAME="your_database_name"                    # Your database name
ENCRYPTION_SECRET="your-32-character-secret-key-here"   # MUST match Node.js backend!
```

### MongoDB URI Examples:

**Local MongoDB:**
```bash
MONGODB_URI="mongodb://localhost:27017/whatsapp"
MONGODB_DB_NAME="whatsapp"
```

**MongoDB Atlas:**
```bash
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority"
MONGODB_DB_NAME="your_db_name"
```

**MongoDB with Authentication:**
```bash
MONGODB_URI="mongodb://username:password@localhost:27017/whatsapp?authSource=admin"
MONGODB_DB_NAME="whatsapp"
```

### Encryption Secret

⚠️ **IMPORTANT:** The `ENCRYPTION_SECRET` must match the secret used in your Node.js backend!

```bash
ENCRYPTION_SECRET="your-exact-secret-from-nodejs-backend"
```

---

## Step 2: Create MongoDB Indexes

Once you've configured MongoDB credentials, run:

```bash
python scripts/setup_mongodb_indexes.py
```

This will:
- ✅ Connect to your MongoDB
- ✅ Create performance indexes
- ✅ Verify everything is set up correctly

Expected output:
```
============================================================
MongoDB Index Setup for WhatsApp Multi-Business
============================================================
Connecting to MongoDB...
✅ Connected to MongoDB successfully

Creating indexes...
1. Creating webhook_lookup_idx...
   ✅ webhook_lookup_idx created
2. Creating subdomain_lookup_idx...
   ✅ subdomain_lookup_idx created
3. Creating active_businesses_idx...
   ✅ active_businesses_idx created

✅ Index setup completed successfully!
```

---

## Step 3: Test the Optimized Service

Start the server:

```bash
python -m uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint_optimized:app --reload
```

### Test Health Endpoints

Open a new terminal and run:

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Metrics
curl http://localhost:8000/metrics
```

Expected responses:

**Health:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "database": "healthy",
  "service": "whatsapp-webhook"
}
```

**Metrics:**
```json
{
  "cache": {
    "size": 0,
    "max_size": 1000,
    "ttl_seconds": 300
  },
  "connection_pool": {
    "max_pool_size": 100,
    "min_pool_size": 10
  }
}
```

---

## Step 4: Test Business Lookup

Create a test file `test_business_lookup.py`:

```python
import asyncio
from dotenv import load_dotenv
load_load_dotenv()

from src.ai_companion.services.business_service_optimized import get_optimized_business_service

async def test():
    service = await get_optimized_business_service()

    # Replace with your actual phone number ID from MongoDB
    phone_number_id = "YOUR_PHONE_NUMBER_ID_HERE"

    print(f"Looking up business for phone number ID: {phone_number_id}")

    business = await service.get_business_by_phone_number_id(phone_number_id)

    if business:
        print(f"\n✅ Business found!")
        print(f"  Name: {business['name']}")
        print(f"  Subdomain: {business['subDomain']}")
        print(f"  Token (first 20 chars): {business['decryptedAccessToken'][:20]}...")
    else:
        print(f"\n❌ No business found for phone number ID: {phone_number_id}")
        print("\nTroubleshooting:")
        print("1. Check that the phone_number_id exists in your MongoDB")
        print("2. Verify whatsappEnabled=true and isActive=true")
        print("3. Run: python scripts/extractWhatsAppCredentials.ts")

    await service.disconnect()

asyncio.run(test())
```

Run:
```bash
python test_business_lookup.py
```

---

## Step 5: Production Deployment

Once everything is working locally:

```bash
# Install gunicorn
pip install gunicorn

# Run with production settings
gunicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint_optimized:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30
```

---

## Troubleshooting

### "MONGODB_URI not set"

Make sure you've filled in the MongoDB credentials in `.env`:

```bash
# Check if variables are set
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('MONGODB_URI:', 'SET' if os.getenv('MONGODB_URI') else 'NOT SET')
print('MONGODB_DB_NAME:', 'SET' if os.getenv('MONGODB_DB_NAME') else 'NOT SET')
print('ENCRYPTION_SECRET:', 'SET' if os.getenv('ENCRYPTION_SECRET') else 'NOT SET')
"
```

### "Connection failed"

1. Check MongoDB is running:
   ```bash
   # For local MongoDB
   mongosh --eval "db.runCommand({ping: 1})"
   ```

2. Test connection string:
   ```bash
   mongosh "YOUR_MONGODB_URI" --eval "db.runCommand({ping: 1})"
   ```

### "No business found"

1. Check your MongoDB has businesses:
   ```bash
   mongosh "YOUR_MONGODB_URI"
   > use your_database_name
   > db.businesses.find({whatsappEnabled: true}).count()
   ```

2. Extract credentials to verify:
   ```bash
   npx ts-node scripts/extractWhatsAppCredentials.ts
   ```

### "Decryption failed"

Make sure `ENCRYPTION_SECRET` matches your Node.js backend exactly!

---

## Performance Verification

### Check Cache Performance

```bash
# Let it run for a few minutes, then check metrics
curl http://localhost:8000/metrics
```

Look for:
- `cache.size` should grow as businesses are accessed
- Cache should stabilize at frequently-used businesses

### Monitor Logs

```bash
# In your server terminal, look for:
✅ "Cache HIT" - Good! (should be 95%+ after warmup)
⚠️  "Cache MISS" - Expected for first request per business
✅ "Cache warmed up with X businesses" - On startup
```

---

## Next Steps

1. ✅ Fill in `.env` with MongoDB credentials
2. ✅ Run `python scripts/setup_mongodb_indexes.py`
3. ✅ Start server and test endpoints
4. ✅ Test business lookup
5. ✅ Deploy to production

---

## Need Help?

- **Setup Issues:** Check [WHATSAPP_MULTI_BUSINESS_SETUP.md](docs/WHATSAPP_MULTI_BUSINESS_SETUP.md)
- **Performance:** Check [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
- **Migration:** Check [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md)
