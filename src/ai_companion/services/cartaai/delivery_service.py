"""Delivery service for handling zone-based delivery cost calculations.

This service provides high-level methods for:
- Validating delivery zones
- Calculating delivery costs
- Formatting delivery information for display
"""

import logging
from typing import Dict, Any, Optional, Tuple
from ai_companion.services.cartaai.client import CartaAIClient, CartaAIAPIException

logger = logging.getLogger(__name__)


class DeliveryService:
    """Service for managing delivery zone validation and cost calculation."""

    def __init__(self, client: CartaAIClient, restaurant_lat: float, restaurant_lng: float):
        """Initialize delivery service.

        Args:
            client: CartaAI API client instance
            restaurant_lat: Restaurant latitude coordinate
            restaurant_lng: Restaurant longitude coordinate
        """
        self.client = client
        self.restaurant_lat = restaurant_lat
        self.restaurant_lng = restaurant_lng
        self._zone_cache: Optional[Dict[str, Any]] = None

    async def validate_delivery_zone(
        self, delivery_lat: float, delivery_lng: float
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate if a delivery location is within a serviceable zone.

        According to requirements:
        - A delivery address can only fall into ONE zone (not multiple)
        - If out of zone, automatically suggest pickup

        Args:
            delivery_lat: Delivery location latitude
            delivery_lng: Delivery location longitude

        Returns:
            Tuple of (is_valid, zone_data, error_message):
                - is_valid: True if location is in a delivery zone
                - zone_data: Zone information including cost, or None if invalid
                - error_message: Error description if invalid, or None if valid
        """
        try:
            result = await self.client.calculate_delivery_cost(
                restaurant_lat=self.restaurant_lat,
                restaurant_lng=self.restaurant_lng,
                delivery_lat=delivery_lat,
                delivery_lng=delivery_lng,
            )

            if result.get("type") == "1" and result.get("data"):
                data = result["data"]
                zone_info = {
                    "distance": data.get("distance"),
                    "zone": data.get("zone"),
                    "deliveryCost": data.get("deliveryCost"),
                    "estimatedTime": data.get("estimatedTime"),
                    "meetsMinimum": data.get("meetsMinimum", True),
                }
                return True, zone_info, None
            else:
                error_msg = result.get("message", "Unknown error")
                return False, None, error_msg

        except CartaAIAPIException as e:
            logger.warning(f"Delivery zone validation failed: {e}")
            if e.status_code == 404:
                return False, None, "No delivery zone found for this location"
            return False, None, f"Validation error: {e.message}"
        except Exception as e:
            logger.error(f"Unexpected error validating delivery zone: {e}")
            return False, None, "Unable to validate delivery location"

    async def get_delivery_cost(
        self, delivery_lat: float, delivery_lng: float
    ) -> Optional[Dict[str, Any]]:
        """Get delivery cost for a specific location.

        Args:
            delivery_lat: Delivery location latitude
            delivery_lng: Delivery location longitude

        Returns:
            Dictionary with delivery information:
            {
                "cost": 5.0,
                "distance": 1.23,
                "zone_name": "City-Wide Delivery",
                "estimated_time": 30,
                "meets_minimum": True,
                "allows_free_delivery": False,
                "minimum_for_free_delivery": 0.0
            }
            Returns None if location is not serviceable.
        """
        is_valid, zone_data, _ = await self.validate_delivery_zone(delivery_lat, delivery_lng)

        if not is_valid or not zone_data:
            return None

        zone = zone_data.get("zone", {})

        return {
            "cost": zone_data.get("deliveryCost", 0.0),
            "distance": zone_data.get("distance", 0.0),
            "zone_name": zone.get("zoneName", "Unknown Zone"),
            "zone_id": zone.get("_id"),
            "estimated_time": zone_data.get("estimatedTime", 30),
            "meets_minimum": zone_data.get("meetsMinimum", True),
            "minimum_order": zone.get("minimumOrder", 0.0),
            # Free delivery logic based on allowsFreeDelivery flag
            "allows_free_delivery": zone.get("allowsFreeDelivery", False),
            "minimum_for_free_delivery": zone.get("minimumForFreeDelivery", 0.0),
        }

    def format_delivery_info(self, delivery_info: Dict[str, Any], subtotal: float = 0.0) -> str:
        """Format delivery information for display to user.

        Requirements:
        - Display distance in KM
        - Display delivery fee
        - Use zone's allowsFreeDelivery flag for free delivery logic

        Args:
            delivery_info: Delivery information from get_delivery_cost()
            subtotal: Order subtotal to check free delivery eligibility

        Returns:
            Formatted string for user display
        """
        distance = delivery_info.get("distance", 0.0)
        cost = delivery_info.get("cost", 0.0)
        zone_name = delivery_info.get("zone_name", "Unknown")
        estimated_time = delivery_info.get("estimated_time", 30)
        allows_free_delivery = delivery_info.get("allows_free_delivery", False)
        min_for_free = delivery_info.get("minimum_for_free_delivery", 0.0)

        # Determine actual delivery fee based on free delivery logic
        actual_fee = cost
        free_delivery_applied = False

        if allows_free_delivery and min_for_free > 0 and subtotal >= min_for_free:
            actual_fee = 0.0
            free_delivery_applied = True

        lines = [
            f"📍 **Zone de livraison:** {zone_name}",
            f"📏 **Distance:** {distance:.2f} km",
        ]

        if free_delivery_applied:
            lines.append(f"🎉 **Frais de livraison:** GRATUIT (économisez ${cost:.2f})")
        else:
            lines.append(f"💰 **Frais de livraison:** ${actual_fee:.2f}")

        lines.append(f"⏰ **Temps estimé:** {estimated_time} minutes")

        # Show free delivery threshold if applicable
        if allows_free_delivery and min_for_free > 0 and not free_delivery_applied:
            remaining = min_for_free - subtotal
            if remaining > 0:
                lines.append(
                    f"\n💡 *Ajoutez ${remaining:.2f} pour la livraison gratuite!*"
                )

        return "\n".join(lines)

    def format_out_of_zone_message(self, distance: Optional[float] = None) -> str:
        """Format message when delivery location is out of service area.

        Requirements:
        - Automatically suggest pickup as alternative

        Args:
            distance: Distance to the location (if available)

        Returns:
            Formatted message with pickup suggestion
        """
        lines = [
            "❌ **Désolé, zone non couverte**",
            "",
        ]

        if distance:
            lines.append(f"📏 Distance: {distance:.2f} km")
            lines.append("")

        lines.extend([
            "🚫 Nous ne livrons pas à cette adresse pour le moment.",
            "",
            "✅ **Alternative suggérée:**",
            "🏃 Optez pour le **ramassage** au restaurant",
            "",
            "Souhaitez-vous continuer avec le ramassage?"
        ])

        return "\n".join(lines)

    async def get_all_zones(self) -> Optional[Dict[str, Any]]:
        """Get all delivery zones for the restaurant.

        Returns:
            Dictionary with zones data, or None on error
        """
        try:
            result = await self.client.get_delivery_zones()
            if result.get("type") == "1":
                self._zone_cache = result
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching delivery zones: {e}")
            return None

    def calculate_final_delivery_fee(
        self,
        base_cost: float,
        subtotal: float,
        allows_free_delivery: bool,
        minimum_for_free_delivery: float,
    ) -> Tuple[float, Optional[str]]:
        """Calculate final delivery fee with free delivery logic.

        Requirements:
        - Use zone's allowsFreeDelivery flag
        - Apply free delivery if subtotal meets minimum

        Args:
            base_cost: Base delivery cost from zone
            subtotal: Order subtotal
            allows_free_delivery: Zone's allowsFreeDelivery flag
            minimum_for_free_delivery: Minimum order for free delivery

        Returns:
            Tuple of (final_fee, discount_description):
                - final_fee: Actual delivery fee after free delivery logic
                - discount_description: Description if free delivery applied
        """
        if allows_free_delivery and minimum_for_free_delivery > 0:
            if subtotal >= minimum_for_free_delivery:
                return 0.0, f"Free delivery (minimum ${minimum_for_free_delivery:.2f} met)"

        return base_cost, None
