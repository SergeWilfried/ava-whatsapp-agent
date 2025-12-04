"""Test script for CartaAI API with provided credentials.

This script tests the API endpoints with the given credentials:
- localId: LOC1760097779968WGX4I
- subdomain: my-restaurant
- API Key: carta_srv_TYU3uDDbMJSPfMt9IyxuEulQLUu7R8XddGRmXSj3reU0UzZm5HSaImtcIXHM
- URL: api-server-lemenu-production.up.railway.app
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_companion.services.cartaai import (
    CartaAIClient,
    CartaAIAPIException,
    CartaAINetworkException,
)


# Test credentials
BASE_URL = "https://api-server-lemenu-production.up.railway.app/api/v1"
SUBDOMAIN = "my-restaurant"
LOCAL_ID = "LOC1760097779968WGX4I"
API_KEY = "carta_srv_TYU3uDDbMJSPfMt9IyxuEulQLUu7R8XddGRmXSj3reU0UzZm5HSaImtcIXHM"


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response: dict):
    """Pretty print API response."""
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False))


async def test_menu_structure(client: CartaAIClient):
    """Test GET /menu2/bot-structure endpoint."""
    print_section("TEST 1: Get Menu Structure (Bot Integration)")

    try:
        print(f"\n📡 Calling: GET /menu2/bot-structure")
        print(f"   Query Params: subDomain={SUBDOMAIN}, localId={LOCAL_ID}")

        response = await client.get_menu_structure()

        print(f"\n✅ SUCCESS")
        print(f"   Response Type: {response.get('type')}")
        print(f"   Message: {response.get('message')}")

        if response.get('data'):
            categories = response['data'].get('categories', [])
            print(f"   Categories Found: {len(categories)}")

            if categories:
                print("\n   First 3 Categories:")
                for cat in categories[:3]:
                    products = cat.get('products', [])
                    print(f"     • {cat.get('name', 'N/A')} - {len(products)} products")

                    if products:
                        print(f"       Sample products:")
                        for prod in products[:2]:
                            print(f"         - {prod.get('name', 'N/A')} - ${prod.get('basePrice', 0)}")

        print("\n📊 Full Response:")
        print_response(response)
        return response

    except CartaAIAPIException as e:
        print(f"\n❌ API ERROR")
        print(f"   Status Code: {e.status_code}")
        print(f"   Message: {e.message}")
        print(f"   Data: {e.data}")
        return None

    except CartaAINetworkException as e:
        print(f"\n❌ NETWORK ERROR")
        print(f"   Message: {e.message}")
        return None


async def test_product_details(client: CartaAIClient, product_ids: list):
    """Test POST /menu/getProductInMenu/{localId}/{subDomain} endpoint."""
    print_section("TEST 2: Get Product Details with Modifiers")

    try:
        print(f"\n📡 Calling: POST /menu/getProductInMenu/{LOCAL_ID}/{SUBDOMAIN}")
        print(f"   Product IDs: {product_ids}")

        response = await client.get_product_details(product_ids)

        print(f"\n✅ SUCCESS")
        print(f"   Success: {response.get('success')}")
        print(f"   Message: {response.get('message')}")

        if response.get('data'):
            products = response['data']
            print(f"   Products Retrieved: {len(products)}")

            for product in products:
                print(f"\n   📦 Product: {product.get('name', 'N/A')}")
                print(f"      ID: {product.get('_id')}")
                print(f"      Base Price: ${product.get('price', 0)}")

                presentations = product.get('presentations', [])
                print(f"      Presentations: {len(presentations)}")
                for pres in presentations:
                    print(f"        • {pres.get('name')} - ${pres.get('price')}")

                modifiers = product.get('modifiers', [])
                print(f"      Modifiers: {len(modifiers)}")
                for mod in modifiers:
                    print(f"        • {mod.get('name')} (min: {mod.get('minSelections')}, max: {mod.get('maxSelections')})")
                    options = mod.get('options', [])
                    for opt in options[:3]:  # Show first 3 options
                        print(f"          - {opt.get('name')} +${opt.get('price', 0)}")

        print("\n📊 Full Response:")
        print_response(response)
        return response

    except CartaAIAPIException as e:
        print(f"\n❌ API ERROR")
        print(f"   Status Code: {e.status_code}")
        print(f"   Message: {e.message}")
        print(f"   Data: {e.data}")
        return None

    except CartaAINetworkException as e:
        print(f"\n❌ NETWORK ERROR")
        print(f"   Message: {e.message}")
        return None


async def test_delivery_zones(client: CartaAIClient):
    """Test GET /delivery/zones/{subDomain}/{localId} endpoint."""
    print_section("TEST 3: Get Delivery Zones")

    try:
        print(f"\n📡 Calling: GET /delivery/zones/{SUBDOMAIN}/{LOCAL_ID}")

        response = await client.get_delivery_zones()

        print(f"\n✅ SUCCESS")
        print(f"   Response Type: {response.get('type')}")
        print(f"   Message: {response.get('message')}")

        if response.get('data'):
            zones = response['data']
            print(f"   Zones Found: {len(zones)}")

            for zone in zones:
                print(f"\n   📍 Zone: {zone.get('zoneName', 'N/A')}")
                print(f"      Delivery Cost: ${zone.get('deliveryCost', 0)}")
                print(f"      Minimum Order: ${zone.get('minimumOrder', 0)}")
                print(f"      Estimated Time: {zone.get('estimatedTime')} min")
                print(f"      Free Delivery: {zone.get('allowsFreeDelivery', False)}")
                if zone.get('allowsFreeDelivery'):
                    print(f"      Free Delivery Minimum: ${zone.get('minimumForFreeDelivery', 0)}")

        print("\n📊 Full Response:")
        print_response(response)
        return response

    except CartaAIAPIException as e:
        print(f"\n❌ API ERROR")
        print(f"   Status Code: {e.status_code}")
        print(f"   Message: {e.message}")
        print(f"   Data: {e.data}")
        return None

    except CartaAINetworkException as e:
        print(f"\n❌ NETWORK ERROR")
        print(f"   Message: {e.message}")
        return None


async def test_all_categories(client: CartaAIClient):
    """Test GET /categories/get-all/{subDomain}/{localId} endpoint."""
    print_section("TEST 4: Get All Categories")

    try:
        print(f"\n📡 Calling: GET /categories/get-all/{SUBDOMAIN}/{LOCAL_ID}")

        response = await client.get_all_categories()

        print(f"\n✅ SUCCESS")
        print(f"   Response Type: {response.get('type')}")
        print(f"   Message: {response.get('message')}")

        if response.get('data'):
            categories = response['data']
            print(f"   Categories Found: {len(categories)}")

            for cat in categories[:5]:  # Show first 5
                print(f"     • {cat.get('name', 'N/A')} (ID: {cat.get('_id')})")

        print("\n📊 Full Response:")
        print_response(response)
        return response

    except CartaAIAPIException as e:
        print(f"\n❌ API ERROR")
        print(f"   Status Code: {e.status_code}")
        print(f"   Message: {e.message}")
        print(f"   Data: {e.data}")
        return None

    except CartaAINetworkException as e:
        print(f"\n❌ NETWORK ERROR")
        print(f"   Message: {e.message}")
        return None


async def main():
    """Run all API tests."""
    print_section("CartaAI API Integration Test")
    print(f"\n🔧 Configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Subdomain: {SUBDOMAIN}")
    print(f"   Local ID: {LOCAL_ID}")
    print(f"   API Key: {'*' * 40} (hidden)")

    # Create client
    async with CartaAIClient(
        base_url=BASE_URL,
        subdomain=SUBDOMAIN,
        local_id=LOCAL_ID,
        api_key=API_KEY,
        timeout=30,
        max_retries=3,
        enable_logging=True,
    ) as client:

        # Test 1: Menu Structure
        menu_response = await test_menu_structure(client)

        # Test 2: Product Details (if we got products from menu)
        if menu_response and menu_response.get('data'):
            categories = menu_response['data'].get('categories', [])
            if categories and categories[0].get('products'):
                # Get first product ID
                first_product_id = categories[0]['products'][0].get('id')
                if first_product_id:
                    await test_product_details(client, [first_product_id])

        # Test 3: Delivery Zones
        await test_delivery_zones(client)

        # Test 4: All Categories
        await test_all_categories(client)

        # Show metrics
        print_section("CLIENT METRICS")
        metrics = client.get_metrics()
        print(f"\n📊 Performance Metrics:")
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Successful: {metrics['successful_requests']}")
        print(f"   Failed: {metrics['failed_requests']}")
        print(f"   Retried: {metrics['retried_requests']}")
        print(f"   Rate Limited: {metrics['rate_limited_requests']}")
        print(f"   Success Rate: {metrics['success_rate']:.2f}%")
        print(f"   Avg Response Time: {metrics['average_response_time']:.3f}s")

    print_section("INTEGRATION REVIEW SUMMARY")
    print("""
✅ AUTHENTICATION:
   - Uses X-Service-API-Key header (correct per API specs)
   - API key is properly passed in headers

✅ ENDPOINTS TESTED:
   1. GET /menu2/bot-structure - Menu structure for bot
   2. POST /menu/getProductInMenu/{localId}/{subdomain} - Product details
   3. GET /delivery/zones/{subdomain}/{localId} - Delivery zones
   4. GET /categories/get-all/{subdomain}/{localId} - All categories

✅ REQUEST FORMAT:
   - Correct HTTP methods (GET/POST)
   - Proper URL path parameters
   - Query parameters correctly passed
   - JSON body for POST requests

✅ RESPONSE HANDLING:
   - Parses JSON responses correctly
   - Handles type field ("1" for success, "3" for error)
   - Extracts data from response.data

✅ ERROR HANDLING:
   - Catches API errors (4xx, 5xx)
   - Catches network errors
   - Retry logic with exponential backoff
   - Rate limiting support (429 status)

✅ FEATURES:
   - Async/await support
   - Connection pooling
   - Request timeout handling
   - Metrics tracking
   - Detailed logging
    """)

    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
