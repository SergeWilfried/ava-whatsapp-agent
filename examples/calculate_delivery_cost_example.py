#!/usr/bin/env python3
"""Example: Calculate delivery cost using mileage-based zones.

This example demonstrates how to use the calculate_delivery_cost() method
to get zone-based delivery pricing from the CartaAI API.
"""

import asyncio
import os
from ai_companion.services.cartaai.client import CartaAIClient


async def main():
    """Calculate delivery cost for a sample location."""

    # Configuration from environment
    config = {
        "base_url": os.getenv("CARTAAI_API_BASE_URL", "https://api-server-lemenu-production.up.railway.app/api/v1"),
        "subdomain": os.getenv("CARTAAI_SUBDOMAIN", "my-restaurant"),
        "local_id": os.getenv("CARTAAI_LOCAL_ID", "LOC1760097779968WGX4I"),
        "api_key": os.getenv("CARTAAI_API_KEY"),
    }

    # Restaurant location (example: Lima, Peru)
    restaurant_lat = -12.0464
    restaurant_lng = -77.0428

    # Delivery location (example: ~1.2 km away)
    delivery_lat = -12.0564
    delivery_lng = -77.0528

    async with CartaAIClient(**config) as client:
        try:
            print("🚚 Calculating delivery cost...")
            print(f"📍 Restaurant: ({restaurant_lat}, {restaurant_lng})")
            print(f"📍 Delivery: ({delivery_lat}, {delivery_lng})")
            print()

            # Calculate delivery cost
            result = await client.calculate_delivery_cost(
                restaurant_lat=restaurant_lat,
                restaurant_lng=restaurant_lng,
                delivery_lat=delivery_lat,
                delivery_lng=delivery_lng,
            )

            if result["type"] == "1":
                data = result["data"]
                zone = data["zone"]

                print("✅ Delivery cost calculated successfully!")
                print()
                print(f"📏 Distance: {data['distance']:.2f} km")
                print(f"💰 Delivery Cost: ${data['deliveryCost']:.2f}")
                print(f"⏰ Estimated Time: {data['estimatedTime']} minutes")
                print()
                print(f"📦 Zone: {zone['zoneName']}")
                print(f"   Type: {zone['type']}")
                print(f"   Base Cost: ${zone['baseCost']}")
                print(f"   Base Distance: {zone['baseDistance']} km")
                print(f"   Incremental Cost: ${zone['incrementalCost']}")
                print(f"   Distance Increment: {zone['distanceIncrement']} km")
                print(f"   Minimum Order: ${zone['minimumOrder']}")
                print()

                if data.get("meetsMinimum"):
                    print("✅ Meets minimum order requirement")
                else:
                    print("⚠️  Does not meet minimum order requirement")
            else:
                print(f"❌ Error: {result['message']}")

        except Exception as e:
            print(f"❌ Error calculating delivery cost: {e}")


if __name__ == "__main__":
    asyncio.run(main())
