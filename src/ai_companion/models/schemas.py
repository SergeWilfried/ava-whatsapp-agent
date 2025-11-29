"""
MongoDB schemas for e-commerce collections.
These map to the same collections used by the Node.js backend.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProductModifier(BaseModel):
    """Product modifier schema"""
    id: str
    name: str
    price: float
    is_required: bool = False
    is_active: bool = True


class NutritionalInfo(BaseModel):
    """Nutritional information schema"""
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class Product(BaseModel):
    """Product schema - maps to MongoDB products collection"""
    r_id: str = Field(alias="rId")
    name: str
    description: Optional[str] = None
    category_id: str = Field(alias="categoryId")
    category: str
    base_price: float = Field(alias="basePrice")
    is_combo: bool = Field(default=False, alias="isCombo")
    is_out_of_stock: bool = Field(default=False, alias="isOutOfStock")
    is_available: bool = Field(default=True, alias="isAvailable")
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    modifiers: List[ProductModifier] = []
    presentations: List[str] = []
    tags: List[str] = []
    sub_domain: str = Field(alias="subDomain")
    local_id: str = Field(alias="localId")
    is_active: bool = Field(default=True, alias="isActive")
    nutritional_info: Optional[NutritionalInfo] = Field(default=None, alias="nutritionalInfo")
    allergens: List[str] = []
    preparation_time: int = Field(default=0, alias="preparationTime")
    is_featured: bool = Field(default=False, alias="isFeatured")
    sort_order: int = Field(default=0, alias="sortOrder")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Presentation(BaseModel):
    """Product presentation/variant schema"""
    r_id: str = Field(alias="rId")
    name: str
    price: float
    discounted_price: Optional[float] = Field(default=None, alias="discountedPrice")
    is_default: bool = Field(default=False, alias="isDefault")
    is_active: bool = Field(default=True, alias="isActive")
    product_id: str = Field(alias="productId")

    class Config:
        populate_by_name = True


class ModifierOption(BaseModel):
    """Modifier option schema"""
    option_id: str = Field(alias="optionId")
    name: str
    price: float
    is_active: bool = Field(default=True, alias="isActive")

    class Config:
        populate_by_name = True


class Modifier(BaseModel):
    """Modifier group schema"""
    r_id: str = Field(alias="rId")
    name: str
    is_multiple: bool = Field(alias="isMultiple")
    min_quantity: int = Field(default=0, alias="minQuantity")
    max_quantity: Optional[int] = Field(default=None, alias="maxQuantity")
    options: List[ModifierOption] = []

    class Config:
        populate_by_name = True


class OrderModifierOption(BaseModel):
    """Order modifier option schema"""
    option_id: str = Field(alias="optionId")
    name: str
    price: float
    quantity: int = 1

    class Config:
        populate_by_name = True


class OrderModifier(BaseModel):
    """Order modifier schema"""
    modifier_id: str = Field(alias="modifierId")
    name: str
    options: List[OrderModifierOption] = []

    class Config:
        populate_by_name = True


class OrderItem(BaseModel):
    """Order item schema"""
    id: str
    product_id: str = Field(alias="productId")
    presentation_id: Optional[str] = Field(default=None, alias="presentationId")
    name: str
    description: Optional[str] = None
    quantity: int = 1
    unit_price: float = Field(alias="unitPrice")
    total_price: float = Field(alias="totalPrice")
    modifiers: List[OrderModifier] = []
    notes: Optional[str] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")

    class Config:
        populate_by_name = True


class Address(BaseModel):
    """Address schema"""
    street: str
    city: str
    state: str
    zip_code: str = Field(alias="zipCode")
    country: str
    coordinates: Optional[Dict[str, float]] = None

    class Config:
        populate_by_name = True


class CustomerInfo(BaseModel):
    """Customer information schema"""
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[Address] = None
    customer_id: Optional[str] = Field(default=None, alias="customerId")
    loyalty_points: int = Field(default=0, alias="loyaltyPoints")

    class Config:
        populate_by_name = True


class DeliveryInfo(BaseModel):
    """Delivery information schema"""
    address: Address
    coordinates: Optional[Dict[str, float]] = None
    delivery_instructions: Optional[str] = Field(default=None, alias="deliveryInstructions")
    estimated_time: int = Field(alias="estimatedTime")  # minutes
    assigned_driver: Optional[Dict[str, str]] = Field(default=None, alias="assignedDriver")
    delivery_company: Optional[Dict[str, str]] = Field(default=None, alias="deliveryCompany")

    class Config:
        populate_by_name = True


class Order(BaseModel):
    """Order schema - maps to MongoDB orders collection"""
    order_number: str = Field(alias="orderNumber")
    customer: CustomerInfo
    items: List[OrderItem]
    subtotal: float
    tax: float = 0.0
    delivery_fee: float = Field(default=0.0, alias="deliveryFee")
    discount: float = 0.0
    total: float
    status: str = "pending"  # pending|confirmed|preparing|ready|dispatched|delivered|cancelled|rejected
    type: str  # delivery|pickup|on_site|scheduled_delivery|scheduled_pickup
    payment_method: str = Field(alias="paymentMethod")  # cash|card|yape|plin|mercado_pago|bank_transfer
    payment_status: str = Field(default="pending", alias="paymentStatus")  # pending|paid|failed|refunded|partial
    source: str = "whatsapp"  # digital_menu|whatsapp|phone|pos|website
    estimated_delivery_time: Optional[datetime] = Field(default=None, alias="estimatedDeliveryTime")
    actual_delivery_time: Optional[datetime] = Field(default=None, alias="actualDeliveryTime")
    notes: Optional[str] = None
    delivery_info: Optional[DeliveryInfo] = Field(default=None, alias="deliveryInfo")
    local_id: str = Field(alias="localId")
    sub_domain: str = Field(alias="subDomain")
    conversation_id: Optional[str] = Field(default=None, alias="conversationId")
    bot_id: Optional[str] = Field(default=None, alias="botId")
    archived: bool = False
    archived_at: Optional[datetime] = Field(default=None, alias="archivedAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Cart(BaseModel):
    """Shopping cart schema"""
    session_id: str = Field(alias="sessionId")
    sub_domain: str = Field(alias="subDomain")
    local_id: str = Field(alias="localId")
    items: List[OrderItem] = []
    subtotal: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    expires_at: datetime = Field(alias="expiresAt")  # Cart expiry (24 hours)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Category(BaseModel):
    """Product category schema"""
    r_id: str = Field(alias="rId")
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    sort_order: int = Field(default=0, alias="sortOrder")
    is_active: bool = Field(default=True, alias="isActive")
    sub_domain: str = Field(alias="subDomain")
    local_id: str = Field(alias="localId")
    fb_catalog_id: Optional[str] = Field(default=None, alias="fbCatalogId")  # Meta catalog ID

    class Config:
        populate_by_name = True
