"""Shopping cart data models for restaurant ordering."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from uuid import uuid4


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"


class OrderStage(Enum):
    """Order workflow stage enumeration."""
    BROWSING = "browsing"
    SELECTING = "selecting"
    CUSTOMIZING = "customizing"
    REVIEWING_CART = "reviewing_cart"
    CHECKOUT = "checkout"
    AWAITING_LOCATION = "awaiting_location"
    AWAITING_PHONE = "awaiting_phone"
    PAYMENT = "payment"
    CONFIRMED = "confirmed"


class DeliveryMethod(Enum):
    """Delivery method enumeration."""
    DELIVERY = "delivery"
    PICKUP = "pickup"
    DINE_IN = "dine_in"


class PaymentMethod(Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    ONLINE = "online"


@dataclass
class CartItemCustomization:
    """Customization options for a cart item."""
    size: Optional[str] = None  # "small", "medium", "large"
    extras: List[str] = field(default_factory=list)  # ["extra_cheese", "mushrooms"]
    special_instructions: Optional[str] = None
    price_adjustment: float = 0.0  # Additional cost for customizations


@dataclass
class CartItem:
    """Individual item in the shopping cart."""
    id: str
    menu_item_id: str
    name: str
    base_price: float
    quantity: int = 1
    customization: Optional[CartItemCustomization] = None

    @property
    def item_total(self) -> float:
        """Calculate total price for this item including customizations."""
        base_total = self.base_price * self.quantity
        if self.customization:
            base_total += self.customization.price_adjustment * self.quantity
        return base_total

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "name": self.name,
            "base_price": self.base_price,
            "quantity": self.quantity,
            "item_total": self.item_total,
            "customization": {
                "size": self.customization.size if self.customization else None,
                "extras": self.customization.extras if self.customization else [],
                "special_instructions": self.customization.special_instructions if self.customization else None,
                "price_adjustment": self.customization.price_adjustment if self.customization else 0.0
            } if self.customization else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CartItem":
        """Create CartItem from dictionary."""
        customization = None
        if data.get("customization"):
            cust_data = data["customization"]
            customization = CartItemCustomization(
                size=cust_data.get("size"),
                extras=cust_data.get("extras", []),
                special_instructions=cust_data.get("special_instructions"),
                price_adjustment=cust_data.get("price_adjustment", 0.0)
            )

        return cls(
            id=data["id"],
            menu_item_id=data["menu_item_id"],
            name=data["name"],
            base_price=data["base_price"],
            quantity=data["quantity"],
            customization=customization
        )


@dataclass
class ShoppingCart:
    """Shopping cart for restaurant orders."""
    cart_id: str = field(default_factory=lambda: str(uuid4()))
    items: List[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def subtotal(self) -> float:
        """Calculate subtotal of all items."""
        return sum(item.item_total for item in self.items)

    @property
    def item_count(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0

    def add_item(self, item: CartItem) -> None:
        """Add item to cart or update quantity if already exists."""
        # Check if exact same item with same customizations exists
        for existing_item in self.items:
            if (existing_item.menu_item_id == item.menu_item_id and
                existing_item.customization == item.customization):
                existing_item.quantity += item.quantity
                self.updated_at = datetime.now()
                return

        # Add as new item
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_item(self, cart_item_id: str) -> bool:
        """Remove item from cart by cart item ID."""
        for i, item in enumerate(self.items):
            if item.id == cart_item_id:
                self.items.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def update_quantity(self, cart_item_id: str, quantity: int) -> bool:
        """Update quantity of a specific item."""
        if quantity <= 0:
            return self.remove_item(cart_item_id)

        for item in self.items:
            if item.id == cart_item_id:
                item.quantity = quantity
                self.updated_at = datetime.now()
                return True
        return False

    def clear(self) -> None:
        """Clear all items from cart."""
        self.items = []
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert cart to dictionary for serialization."""
        return {
            "cart_id": self.cart_id,
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ShoppingCart":
        """Create ShoppingCart from dictionary."""
        from datetime import datetime

        cart = cls(cart_id=data["cart_id"])
        cart.items = [CartItem.from_dict(item_data) for item_data in data.get("items", [])]
        cart.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        cart.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()

        return cart


@dataclass
class Order:
    """Complete order with delivery and payment information."""
    order_id: str = field(default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}")
    cart: ShoppingCart = field(default_factory=ShoppingCart)
    status: OrderStatus = OrderStatus.PENDING
    delivery_method: Optional[DeliveryMethod] = None
    payment_method: Optional[PaymentMethod] = None

    # Customer and delivery information
    delivery_address: Optional[str] = None
    customer_phone: Optional[str] = None  # Required for all order types (delivery, pickup, dine-in)
    customer_name: Optional[str] = None

    # API integration fields
    api_order_id: Optional[str] = None  # CartaAI API order ID
    api_order_number: Optional[str] = None  # CartaAI order number (e.g., "ORD-2024-001234")

    # Pricing
    subtotal: float = 0.0
    tax_rate: float = 0.08
    delivery_fee: float = 0.0
    discount: float = 0.0
    discount_description: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    estimated_ready_time: Optional[datetime] = None

    # Notes
    special_instructions: Optional[str] = None

    @property
    def tax_amount(self) -> float:
        """Calculate tax amount."""
        return self.subtotal * self.tax_rate

    @property
    def total(self) -> float:
        """Calculate total order amount."""
        return self.subtotal + self.tax_amount + self.delivery_fee - self.discount

    def calculate_totals(self, tax_rate: float, delivery_fee: float, free_delivery_minimum: float) -> None:
        """Calculate all totals based on cart and settings."""
        self.subtotal = self.cart.subtotal
        self.tax_rate = tax_rate

        # Apply free delivery if applicable
        if self.subtotal >= free_delivery_minimum:
            self.delivery_fee = 0.0
            self.discount_description = "Free delivery"
        else:
            self.delivery_fee = delivery_fee if self.delivery_method == DeliveryMethod.DELIVERY else 0.0

    def to_dict(self) -> Dict:
        """Convert order to dictionary for serialization."""
        return {
            "order_id": self.order_id,
            "status": self.status.value,
            "cart": self.cart.to_dict(),
            "delivery_method": self.delivery_method.value if self.delivery_method else None,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "delivery_address": self.delivery_address,
            "customer_phone": self.customer_phone,
            "customer_name": self.customer_name,
            "api_order_id": self.api_order_id,
            "api_order_number": self.api_order_number,
            "subtotal": self.subtotal,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "delivery_fee": self.delivery_fee,
            "discount": self.discount,
            "discount_description": self.discount_description,
            "total": self.total,
            "created_at": self.created_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "special_instructions": self.special_instructions
        }
