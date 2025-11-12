"""
Setup MongoDB indexes for optimized performance (Windows compatible)
Checks existing indexes and only creates missing ones
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_index_exists(collection, index_name: str) -> bool:
    """Check if an index with the given name exists"""
    indexes = await collection.list_indexes().to_list(length=None)
    return any(idx.get('name') == index_name for idx in indexes)

async def create_index_if_missing(collection, index_spec, name: str, **kwargs):
    """Create index only if it doesn't exist"""
    exists = await check_index_exists(collection, name)

    if exists:
        print(f"   [SKIP] {name} already exists")
        return False
    else:
        await collection.create_index(index_spec, name=name, **kwargs)
        print(f"   [OK] {name} created")
        return True

async def setup_indexes():
    """Create MongoDB indexes for optimal performance"""

    mongodb_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")

    if not mongodb_uri:
        print("[ERROR] MONGODB_URI not set in .env file")
        print("Please set MONGODB_URI in your .env file")
        return False

    if not db_name:
        print("[ERROR] MONGODB_DB_NAME not set in .env file")
        print("Please set MONGODB_DB_NAME in your .env file")
        return False

    print(f"Connecting to MongoDB...")
    print(f"Database: {db_name}")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client[db_name]

        # Verify connection
        await client.admin.command('ping')
        print("[OK] Connected to MongoDB successfully")

        # Get businesses collection
        businesses = db.businesses

        # Check existing indexes first
        print("\n" + "="*60)
        print("Checking existing indexes...")
        print("="*60)
        existing_indexes = await businesses.list_indexes().to_list(length=None)
        print(f"Found {len(existing_indexes)} existing indexes:")
        for idx in existing_indexes:
            print(f"  * {idx['name']}")

        print("\n" + "="*60)
        print("Creating missing indexes for webhook optimization...")
        print("="*60)

        created_count = 0

        # Index 1: Webhook lookup (CRITICAL for performance)
        print("\n1. Checking webhook_lookup_idx...")
        if await create_index_if_missing(
            businesses,
            [
                ("whatsappPhoneNumberIds", 1),
                ("whatsappEnabled", 1),
                ("isActive", 1)
            ],
            name="webhook_lookup_idx",
            background=True
        ):
            created_count += 1

        # Index 2: Check if subdomain index exists
        print("\n2. Checking subdomain_lookup_idx...")
        subdomain_exists = await check_index_exists(businesses, "subDomain_1")

        if subdomain_exists:
            print("   [SKIP] subdomain index already exists (subDomain_1)")
            print("   [INFO] Existing index is sufficient for queries")
        else:
            if await create_index_if_missing(
                businesses,
                [("subDomain", 1), ("isActive", 1)],
                name="subdomain_lookup_idx",
                background=True
            ):
                created_count += 1

        # Index 3: Active WhatsApp businesses (for cache warmup)
        print("\n3. Checking active_whatsapp_businesses_idx...")
        if await create_index_if_missing(
            businesses,
            [
                ("whatsappEnabled", 1),
                ("isActive", 1),
                ("createdAt", -1)
            ],
            name="active_whatsapp_businesses_idx",
            background=True
        ):
            created_count += 1

        # List all indexes after creation
        print("\n" + "="*60)
        print("All indexes on businesses collection:")
        print("="*60)
        indexes = await businesses.list_indexes().to_list(length=None)
        for idx in indexes:
            index_name = idx['name']
            is_new = " [NEW]" if index_name in ["webhook_lookup_idx", "subdomain_lookup_idx", "active_whatsapp_businesses_idx"] else ""
            print(f"  * {index_name}{is_new}")
            if 'key' in idx:
                for key, direction in idx['key'].items():
                    if direction == 1:
                        order = "ASC"
                    elif direction == -1:
                        order = "DESC"
                    elif direction == "text":
                        order = "TEXT"
                    elif direction == "2dsphere":
                        order = "GEOSPATIAL"
                    else:
                        order = str(direction)
                    print(f"    - {key}: {order}")

        # Get collection stats
        print("\n" + "="*60)
        print("Collection Statistics:")
        print("="*60)
        stats = await db.command("collStats", "businesses")
        print(f"  * Total documents: {stats.get('count', 0)}")
        print(f"  * Total size: {stats.get('size', 0) / 1024 / 1024:.2f} MB")
        print(f"  * Total indexes: {stats.get('nindexes', 0)}")
        print(f"  * Index size: {stats.get('totalIndexSize', 0) / 1024 / 1024:.2f} MB")

        # Check if we have businesses with WhatsApp enabled
        print("\n" + "="*60)
        print("WhatsApp Business Check:")
        print("="*60)
        whatsapp_count = await businesses.count_documents({
            "whatsappEnabled": True,
            "isActive": True
        })
        print(f"  * Businesses with WhatsApp enabled: {whatsapp_count}")

        if whatsapp_count == 0:
            print("\n[WARNING] No businesses found with WhatsApp enabled!")
            print("   Make sure your businesses have:")
            print("   - whatsappEnabled: true")
            print("   - isActive: true")
            print("   - whatsappPhoneNumberIds: [...]")
            print("   - whatsappAccessToken: <encrypted token>")

        # Close connection
        client.close()

        print("\n" + "="*60)
        if created_count > 0:
            print(f"[OK] Index setup completed! Created {created_count} new index(es)")
        else:
            print("[OK] All required indexes already exist!")
        print("="*60)

        print("\nNext steps:")
        print("1. [OK] Webhook handler already updated to use optimized service")
        print("2. Test locally with:")
        print("   python -m uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint_optimized:app --reload")
        print("3. Check health: curl http://localhost:8000/health")
        print("4. Check metrics: curl http://localhost:8000/metrics")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("MongoDB Index Setup for WhatsApp Multi-Business")
    print("="*60)

    success = asyncio.run(setup_indexes())
    sys.exit(0 if success else 1)
