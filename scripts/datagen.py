"""Synthetic e-commerce sales generator (shared by the loader and the CSV writer)."""
import random
from datetime import datetime, timedelta

CATALOG = {
    "Electronics":   [("Wireless Earbuds", 25, 140), ("4K Monitor", 180, 650), ("Smartwatch", 60, 380),
                      ("Bluetooth Speaker", 20, 160), ("Laptop Stand", 15, 60), ("Gaming Mouse", 20, 110)],
    "Fashion":       [("Running Shoes", 40, 160), ("Denim Jacket", 35, 120), ("Leather Wallet", 15, 70),
                      ("Sunglasses", 12, 150), ("Wool Sweater", 30, 110), ("Backpack", 20, 95)],
    "Home & Kitchen":[("Air Fryer", 50, 160), ("Coffee Maker", 30, 250), ("Vacuum Cleaner", 80, 400),
                      ("Knife Set", 25, 140), ("Bedding Set", 30, 130), ("LED Desk Lamp", 12, 55)],
    "Books":         [("Data Science Handbook", 18, 60), ("Sci-Fi Novel", 8, 25), ("Cookbook", 12, 40),
                      ("Business Biography", 10, 30), ("Kids Story Book", 6, 20)],
    "Sports":        [("Yoga Mat", 12, 50), ("Dumbbell Set", 30, 180), ("Cycling Helmet", 25, 120),
                      ("Tennis Racket", 40, 220), ("Camping Tent", 60, 320)],
    "Beauty":        [("Face Serum", 10, 90), ("Hair Dryer", 20, 140), ("Perfume", 25, 180),
                      ("Electric Shaver", 25, 150), ("Makeup Kit", 15, 110)],
    "Toys":          [("Building Blocks", 12, 90), ("RC Car", 20, 110), ("Board Game", 12, 55),
                      ("Puzzle 1000pc", 8, 30), ("Plush Bear", 6, 35)],
}
LOCATIONS = {
    "United States": ["New York", "Los Angeles", "Chicago", "Houston"],
    "United Kingdom": ["London", "Manchester", "Bristol"],
    "Germany": ["Berlin", "Munich", "Hamburg"],
    "India": ["Mumbai", "Delhi", "Bengaluru", "Kolkata"],
    "Canada": ["Toronto", "Vancouver", "Montreal"],
    "Australia": ["Sydney", "Melbourne"],
    "France": ["Paris", "Lyon"],
    "Japan": ["Tokyo", "Osaka"],
}
COUNTRY_W = [30, 14, 10, 16, 8, 6, 8, 8]
PAYMENTS = ["credit_card", "paypal", "debit_card", "upi", "gift_card", "bank_transfer"]
PAY_W = [45, 22, 14, 9, 4, 6]
STATUSES = ["delivered", "shipped", "processing", "cancelled", "returned"]
STATUS_W = [80, 8, 5, 4, 3]

COLUMNS = ["order_id", "order_date", "customer_id", "country", "city", "category", "product",
           "quantity", "unit_price", "discount_pct", "total_amount", "payment_method", "status", "rating"]


def generate_rows(n, seed=42, days=365):
    rnd = random.Random(seed)
    now = datetime.utcnow().replace(microsecond=0)
    start = now - timedelta(days=days)
    categories = list(CATALOG)
    cat_w = [30, 22, 18, 8, 10, 7, 5]
    countries = list(LOCATIONS)
    customers = [f"CUST-{i:05d}" for i in range(1, 4001)]
    cust_country = {c: rnd.choices(countries, COUNTRY_W)[0] for c in customers}
    for i in range(1, n + 1):
        # seasonality: growth over the year, Nov/Dec peak, weekend bump
        while True:
            d = start + timedelta(seconds=rnd.random() * days * 86400)
            growth = 0.6 + 0.8 * ((d - start).days / days)
            season = 1.6 if d.month in (11, 12) else 1.0
            weekday = 1.15 if d.weekday() >= 5 else 1.0
            if rnd.random() < growth * season * weekday / 2.2:
                break
        cust = rnd.choice(customers)
        country = cust_country[cust]
        city = rnd.choice(LOCATIONS[country])
        cat = rnd.choices(categories, cat_w)[0]
        product, lo, hi = rnd.choice(CATALOG[cat])
        unit_price = round(rnd.uniform(lo, hi), 2)
        qty = rnd.choices([1, 2, 3, 4, 5], [58, 22, 10, 6, 4])[0]
        disc = rnd.choices([0, 5, 10, 15, 20, 30], [55, 15, 14, 8, 5, 3])[0]
        total = round(qty * unit_price * (1 - disc / 100), 2)
        status = rnd.choices(STATUSES, STATUS_W)[0]
        rating = rnd.choices([1, 2, 3, 4, 5], [5, 6, 14, 30, 45])[0]
        if status in ("returned", "cancelled"):
            rating = rnd.choice([1, 1, 2, 3])
        yield {
            "order_id": f"ORD-{i:07d}",
            "order_date": d.strftime("%Y-%m-%dT%H:%M:%S"),
            "customer_id": cust, "country": country, "city": city,
            "category": cat, "product": product,
            "quantity": qty, "unit_price": unit_price, "discount_pct": disc,
            "total_amount": total,
            "payment_method": rnd.choices(PAYMENTS, PAY_W)[0],
            "status": status, "rating": rating,
        }
