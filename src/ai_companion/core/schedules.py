# Restaurant Menu
RESTAURANT_MENU = {
    "pizzas": [
        {"name": "Margherita Pizza", "price": 12.99, "description": "Classic tomato sauce, fresh mozzarella, basil"},
        {"name": "Pepperoni Pizza", "price": 14.99, "description": "Tomato sauce, mozzarella, pepperoni"},
        {"name": "Vegetarian Pizza", "price": 13.99, "description": "Bell peppers, mushrooms, olives, onions"},
        {"name": "BBQ Chicken Pizza", "price": 15.99, "description": "BBQ sauce, grilled chicken, red onions, cilantro"},
        {"name": "Hawaiian Pizza", "price": 14.99, "description": "Ham, pineapple, mozzarella"},
    ],
    "burgers": [
        {"name": "Classic Burger", "price": 9.99, "description": "Beef patty, lettuce, tomato, onions, pickles"},
        {"name": "Cheeseburger", "price": 10.99, "description": "Beef patty, cheddar cheese, lettuce, tomato"},
        {"name": "Bacon Burger", "price": 11.99, "description": "Beef patty, bacon, cheddar, BBQ sauce"},
        {"name": "Veggie Burger", "price": 10.49, "description": "Plant-based patty, lettuce, tomato, avocado"},
    ],
    "sides": [
        {"name": "French Fries", "price": 3.99, "description": "Crispy golden fries"},
        {"name": "Onion Rings", "price": 4.49, "description": "Crispy beer-battered onion rings"},
        {"name": "Mozzarella Sticks", "price": 5.99, "description": "6 pieces with marinara sauce"},
        {"name": "Caesar Salad", "price": 6.99, "description": "Romaine, parmesan, croutons, Caesar dressing"},
    ],
    "drinks": [
        {"name": "Coca-Cola", "price": 2.50, "description": "12oz can"},
        {"name": "Sprite", "price": 2.50, "description": "12oz can"},
        {"name": "Iced Tea", "price": 2.99, "description": "Fresh brewed"},
        {"name": "Water", "price": 1.50, "description": "Bottled water"},
    ],
    "desserts": [
        {"name": "Chocolate Brownie", "price": 4.99, "description": "Warm brownie with vanilla ice cream"},
        {"name": "Cheesecake", "price": 5.49, "description": "New York style cheesecake"},
        {"name": "Ice Cream Sundae", "price": 4.49, "description": "Vanilla ice cream with chocolate sauce"},
    ],
}

# Restaurant Business Hours (24-hour format)
BUSINESS_HOURS = {
    "monday": {"open": "11:00", "close": "22:00", "is_open": True},
    "tuesday": {"open": "11:00", "close": "22:00", "is_open": True},
    "wednesday": {"open": "11:00", "close": "22:00", "is_open": True},
    "thursday": {"open": "11:00", "close": "22:00", "is_open": True},
    "friday": {"open": "11:00", "close": "23:00", "is_open": True},
    "saturday": {"open": "11:00", "close": "23:00", "is_open": True},
    "sunday": {"open": "12:00", "close": "21:00", "is_open": True},
}

# Restaurant Information
RESTAURANT_INFO = {
    "name": "Tasty Bites Restaurant",
    "phone": "(555) 123-4567",
    "address": "123 Main Street, Downtown",
    "delivery_available": True,
    "pickup_available": True,
    "delivery_fee": 3.50,
    "free_delivery_minimum": 25.00,
    "tax_rate": 0.08,  # 8% tax
    "payment_methods": ["Cash", "Credit Card", "Debit Card", "Mobile Payment"],
    "estimated_delivery_time": "30-45 minutes",
    "estimated_pickup_time": "15-20 minutes",
}

# Special Offers
SPECIAL_OFFERS = {
    "combo_deals": [
        {"name": "Burger Combo", "price": 13.99, "items": ["Any Burger", "Fries", "Drink"], "savings": 2.50},
        {"name": "Pizza Deal", "price": 17.99, "items": ["Large Pizza", "2 Drinks"], "savings": 3.00},
    ],
    "daily_specials": {
        "monday": "10% off all pizzas",
        "tuesday": "Buy 1 Burger, Get 1 50% off",
        "wednesday": "Free delivery on orders over $20",
        "thursday": "Combo deals $2 off",
        "friday": "Happy Hour: 20% off from 4-6pm",
        "saturday": "Family Special: Large Pizza + 4 Drinks $19.99",
        "sunday": "Free dessert with any order over $30",
    },
}
