"""Example usage of CartaAI API Client.

This script demonstrates how to use the CartaAI client for common operations:
- Fetching menu structure
- Getting product details
- Creating orders
- Tracking order status
- Getting delivery zones

Run with:
    python examples/cartaai_client_example.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_companion.services.cartaai import (
    CartaAIClient,
    CartaAIAPIException,
    CartaAINetworkException,
)


async def example_menu_operations(client: CartaAIClient):
    """Demonstrate menu-related operations."""
    print("\n" + "=" * 60)
    print("📋 MENU OPERATIONS")
    print("=" * 60)

    try:
        # 1. Get menu structure
        print("\n1. Fetching menu structure...")
        menu = await client.get_menu_structure()

        if menu.get("type") == "1":
            categories = menu["data"].get("categories", [])
            print(f"✅ Menu retrieved: {len(categories)} categories")

            for cat in categories[:3]:  # Show first 3
                product_count = len(cat.get("products", []))
                print(f"   • {cat['name']}: {product_count} products")

        # 2. Get all categories
        print("\n2. Fetching all categories...")
        categories_response = await client.get_all_categories()

        if categories_response.get("type") == "1":
            cats = categories_response.get("data", [])
            print(f"✅ {len(cats)} categories retrieved")

        # 3. Get product details
        print("\n3. Fetching product details...")
        # Get first product ID from menu
        if categories and categories[0].get("products"):
            product_id = categories[0]["products"][0]["id"]
            products = await client.get_product_details([product_id])

            if products.get("success"):
                product = products["data"][0]
                print(f"✅ Product: {product['name']}")
                print(f"   Price: S/.{product['price']}")
                print(f"   Presentations: {len(product.get('presentations', []))}")
                print(f"   Modifiers: {len(product.get('modifiers', []))}")

    except CartaAIAPIException as e:
        print(f"❌ API Error: {e.message} (Status: {e.status_code})")
    except CartaAINetworkException as e:
        print(f"❌ Network Error: {e.message}")


async def example_order_operations(client: CartaAIClient):
    """Demonstrate order-related operations."""
    print("\n" + "=" * 60)
    print("🛒 ORDER OPERATIONS")
    print("=" * 60)

    try:
        # Create a test order
        print("\n1. Creating test order...")

        order_data = {
            "customer": {
                "name": "Juan Pérez",
                "phone": "+51987654321",
                "address": {
                    "street": "Av. Larco 1234",
                    "city": "Lima",
                    "district": "Miraflores",
                },
            },
            "items": [
                {
                    "productId": "test_prod_001",
                    "name": "Test Product",
                    "quantity": 1,
                    "unitPrice": 15.99,
                }
            ],
            "type": "delivery",
            "paymentMethod": "cash",
            "source": "whatsapp",
        }

        # Note: This will likely fail in test environment
        # Uncomment to test with real API:
        # order = await client.create_order(order_data)
        # if order.get("type") == "1":
        #     order_id = order["data"]["_id"]
        #     order_number = order["data"]["orderNumber"]
        #     print(f"✅ Order created: {order_number}")
        #     print(f"   Order ID: {order_id}")
        #     print(f"   Status: {order['data']['status']}")
        #     print(f"   Total: S/.{order['data']['total']}")

        print("⏭️  Order creation skipped (demo mode)")

        # 2. Get customer orders
        print("\n2. Fetching customer orders...")
        # Uncomment to test:
        # orders = await client.get_customer_orders(
        #     phone="+51987654321",
        #     status="pending"
        # )
        # if orders.get("type") == "1":
        #     order_list = orders.get("data", [])
        #     print(f"✅ Found {len(order_list)} orders")

        print("⏭️  Customer orders skipped (demo mode)")

    except CartaAIAPIException as e:
        print(f"❌ API Error: {e.message} (Status: {e.status_code})")
    except CartaAINetworkException as e:
        print(f"❌ Network Error: {e.message}")


async def example_delivery_operations(client: CartaAIClient):
    """Demonstrate delivery-related operations."""
    print("\n" + "=" * 60)
    print("🚚 DELIVERY OPERATIONS")
    print("=" * 60)

    try:
        # 1. Get delivery zones
        print("\n1. Fetching delivery zones...")
        zones = await client.get_delivery_zones()

        if zones.get("type") == "1":
            zone_list = zones.get("data", [])
            print(f"✅ {len(zone_list)} delivery zones found")

            for zone in zone_list[:3]:  # Show first 3
                print(f"\n   📍 {zone['zoneName']}")
                print(f"      Delivery fee: S/.{zone['deliveryCost']}")
                print(f"      Minimum order: S/.{zone['minimumOrder']}")
                print(f"      Estimated time: {zone['estimatedTime']} min")

                if zone.get("allowsFreeDelivery"):
                    print(
                        f"      Free delivery over: S/.{zone['minimumForFreeDelivery']}"
                    )

        # 2. Get available drivers
        print("\n2. Checking available drivers...")
        drivers = await client.get_available_drivers()

        if drivers.get("type") == "1":
            driver_list = drivers.get("data", [])
            print(f"✅ {len(driver_list)} drivers available")

            for driver in driver_list[:3]:  # Show first 3
                print(f"   • {driver.get('name', 'Unknown')}")

    except CartaAIAPIException as e:
        print(f"❌ API Error: {e.message} (Status: {e.status_code})")
    except CartaAINetworkException as e:
        print(f"❌ Network Error: {e.message}")


async def example_metrics(client: CartaAIClient):
    """Display client metrics."""
    print("\n" + "=" * 60)
    print("📊 CLIENT METRICS")
    print("=" * 60)

    metrics = client.get_metrics()

    print(f"\nTotal Requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']}")
    print(f"Failed: {metrics['failed_requests']}")
    print(f"Retried: {metrics['retried_requests']}")
    print(f"Rate Limited: {metrics['rate_limited_requests']}")
    print(f"Success Rate: {metrics['success_rate']:.2f}%")
    print(f"Avg Response Time: {metrics['average_response_time']:.3f}s")


async def main():
    """Main example function."""
    print("\n" + "=" * 60)
    print("🍔 CartaAI API Client Example")
    print("=" * 60)

    # Get configuration from environment variables
    base_url = os.getenv(
        "CARTAAI_API_BASE_URL", "https://ssgg.api.cartaai.pe/api/v1"
    )
    subdomain = os.getenv("CARTAAI_SUBDOMAIN", "test-restaurant")
    local_id = os.getenv("CARTAAI_LOCAL_ID", "branch-01")
    api_key = os.getenv("CARTAAI_API_KEY")

    if not api_key:
        print("\n⚠️  WARNING: No API key found!")
        print("Set CARTAAI_API_KEY environment variable to run this example.")
        print("\nExample:")
        print("  export CARTAAI_API_KEY=your_api_key_here")
        print("  python examples/cartaai_client_example.py")
        return

    print(f"\nConfiguration:")
    print(f"  Base URL: {base_url}")
    print(f"  Subdomain: {subdomain}")
    print(f"  Local ID: {local_id}")
    print(f"  API Key: {'*' * 20} (hidden)")

    # Create client with context manager
    async with CartaAIClient(
        base_url=base_url,
        subdomain=subdomain,
        local_id=local_id,
        api_key=api_key,
        timeout=30,
        max_retries=3,
        enable_logging=True,
    ) as client:
        # Run examples
        await example_menu_operations(client)
        await example_delivery_operations(client)
        await example_order_operations(client)
        await example_metrics(client)

    print("\n" + "=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
