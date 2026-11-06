import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
DB_PATH = Path("electronics_shop.db")
START, END = date(2023, 1, 1), date(2026, 9, 30)
N_CUSTOMERS, N_ORDERS = 1500, 5000

FIRST = ["Oliver", "Amelia", "Muhammad", "Aisha", "Harry", "Fatima", "Jack", "Sophie", "Ali", "Emily",
         "Noah", "Priya", "Liam", "Zainab", "Ethan", "Chloe", "Omar", "Grace", "Daniel", "Hannah",
         "Arjun", "Megan", "Bilal", "Lucy", "Callum", "Sara", "Rhys", "Ayesha", "Owen", "Isla",
         "Tariq", "Ffion", "Samuel", "Maryam", "Joshua", "Ella", "Hassan", "Cerys", "Leo", "Nadia"]
LAST = ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Khan", "Thomas", "Roberts",
        "Johnson", "Patel", "Hughes", "Ahmed", "Wright", "Morgan", "Hussain", "Edwards", "Walker", "Lewis",
        "Clarke", "Singh", "Griffiths", "Ali", "Jenkins", "Bennett", "Rees", "Malik", "Phillips", "Shah",
        "Price", "Cooper", "Iqbal", "Powell", "Ward", "Baker", "Chaudhry", "Lloyd", "Hall", "Begum"]
CITIES = {"Cardiff": 18, "London": 22, "Birmingham": 10, "Manchester": 10, "Bristol": 8, "Swansea": 7,
          "Newport": 5, "Leeds": 6, "Glasgow": 6, "Liverpool": 4, "Edinburgh": 4}
TIERS = {"Bronze": 50, "Silver": 28, "Gold": 15, "Platinum": 7}
TIER_ORDER_WEIGHT = {"Bronze": 1, "Silver": 2, "Gold": 4, "Platinum": 8}
DISCOUNT_WEIGHTS = {"Bronze": [90, 10, 0, 0, 0], "Silver": [70, 20, 10, 0, 0],
                    "Gold": [50, 20, 20, 10, 0], "Platinum": [30, 20, 20, 20, 10]}
PAYMENTS = {"Credit Card": 38, "Debit Card": 30, "PayPal": 18, "Apple Pay": 8, "Bank Transfer": 4, "Gift Card": 2}
MONTH_WEIGHT = {11: 2.0, 12: 1.8, 7: 1.2, 1: 1.1}

# category: (price_min, price_max, weight_min_kg, weight_max_kg, models)
CATEGORIES = {
    "Laptops": (450, 2200, 1.0, 2.8, ["Ultrabook 13", "Ultrabook 14", "Pro 15", "Pro 16", "Studio 16", "Air 13", "Flex 14"]),
    "Phones": (120, 1400, 0.15, 0.25, ["X1", "X2 Pro", "Lite", "Max", "Edge", "Note", "Fold"]),
    "Audio": (15, 450, 0.05, 1.2, ["Earbuds", "Over-Ear Headphones", "Soundbar", "Speaker Mini", "Studio Monitor", "Neckband"]),
    "Gaming": (25, 650, 0.1, 4.0, ["Controller", "Headset", "Mechanical Keyboard", "Gaming Mouse", "Capture Card", "Console Dock"]),
    "Home Office": (20, 700, 0.3, 12.0, ["Monitor 24", "Monitor 27", "Webcam HD", "Docking Station", "Ergonomic Mouse", "Desk Lamp"]),
    "Smart Home": (12, 300, 0.1, 2.0, ["Smart Plug", "Video Doorbell", "Thermostat", "LED Strip", "Hub", "Motion Sensor"]),
    "Accessories": (5, 90, 0.02, 0.6, ["USB-C Cable", "Charger 65W", "Phone Case", "Screen Protector", "Power Bank", "Laptop Sleeve", "Card Reader"]),
    "Cameras": (60, 1800, 0.2, 1.6, ["Action Cam", "Mirrorless Body", "Compact Cam", "Tripod", "Gimbal", "Dash Cam"]),
}
PRODUCT_COUNT = {"Laptops": 14, "Phones": 16, "Audio": 18, "Gaming": 14, "Home Office": 14,
                 "Smart Home": 14, "Accessories": 20, "Cameras": 10}
BRANDS = ["Nova", "Apex", "Zenith", "Orbit", "Vertex", "Lumen", "Pulse", "Quanta", "Helix", "Arden"]

SCHEMA = """
CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);
CREATE TABLE customers (
    customer_id      INTEGER PRIMARY KEY,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    email            TEXT NOT NULL UNIQUE,
    city             TEXT NOT NULL,
    membership_tier  TEXT NOT NULL CHECK (membership_tier IN ('Bronze','Silver','Gold','Platinum')),
    signup_date      TEXT NOT NULL,
    birth_year       INTEGER NOT NULL CHECK (birth_year BETWEEN 1920 AND 2008),
    marketing_opt_in INTEGER NOT NULL CHECK (marketing_opt_in IN (0,1))
);
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category_id  INTEGER NOT NULL REFERENCES categories(category_id),
    unit_price   REAL NOT NULL CHECK (unit_price > 0),
    stock_qty    INTEGER NOT NULL CHECK (stock_qty >= 0),
    weight_kg    REAL NOT NULL CHECK (weight_kg > 0)
);
CREATE TABLE orders (
    order_id            INTEGER PRIMARY KEY,
    customer_id         INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date          TEXT NOT NULL,
    payment_method      TEXT NOT NULL,
    order_status        TEXT NOT NULL CHECK (order_status IN ('Processing','Shipped','Delivered','Returned','Cancelled')),
    delivery_days       INTEGER CHECK (delivery_days BETWEEN 0 AND 30),
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5)
);
CREATE TABLE order_items (
    order_id           INTEGER NOT NULL REFERENCES orders(order_id),
    product_id         INTEGER NOT NULL REFERENCES products(product_id),
    quantity           INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_at_sale REAL NOT NULL CHECK (unit_price_at_sale > 0),
    discount_pct       REAL NOT NULL CHECK (discount_pct BETWEEN 0 AND 50),
    PRIMARY KEY (order_id, product_id)
);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_items_product ON order_items(product_id);
"""


def wchoice(mapping):
    return random.choices(list(mapping), list(mapping.values()))[0]


def make_products():
    rows, names = [], set()
    for cat_id, (cat, (pmin, pmax, wmin, wmax, models)) in enumerate(CATEGORIES.items(), start=1):
        for _ in range(PRODUCT_COUNT[cat]):
            while True:
                name = f"{random.choice(BRANDS)} {random.choice(models)} {random.choice(['', 'S', 'Plus', 'GT', '2'])}".strip()
                if name not in names:
                    names.add(name)
                    break
            price = round(pmin + (pmax - pmin) * random.random() ** 2.2) - 0.01
            rows.append((len(rows) + 1, name, cat_id, max(price, 0.99), random.randint(0, 400),
                         round(random.uniform(wmin, wmax), 2)))
    return rows


def make_customers():
    rows, seen = [], set()
    for cid in range(1, N_CUSTOMERS + 1):
        first, last = random.choice(FIRST), random.choice(LAST)
        email = f"{first}.{last}{cid}@example.com".lower()
        assert email not in seen
        seen.add(email)
        signup = date(2022, 1, 1) + timedelta(days=random.randint(0, (date(2026, 8, 31) - date(2022, 1, 1)).days))
        rows.append((cid, first, last, email, wchoice(CITIES), wchoice(TIERS), signup.isoformat(),
                     int(random.triangular(1955, 2004, 1992)), int(random.random() < 0.55)))
    return rows


def random_order_date(lo):
    span = (END - lo).days
    while True:
        d = lo + timedelta(days=random.randint(0, span))
        if random.random() < MONTH_WEIGHT.get(d.month, 1.0) / 2.0:
            return d


def make_orders(customers):
    weights = [TIER_ORDER_WEIGHT[c[5]] for c in customers]
    picks = random.choices(customers, weights, k=N_ORDERS)
    drafts = []
    for c in picks:
        lo = max(date.fromisoformat(c[6]), START)
        drafts.append((random_order_date(lo), c))
    drafts.sort(key=lambda t: t[0])

    rows = []
    for oid, (d, c) in enumerate(drafts, start=1):
        tier = c[5]
        days = rating = None
        if d > END - timedelta(days=10):
            status = random.choice(["Processing", "Shipped"])
        else:
            status = random.choices(["Delivered", "Returned", "Cancelled"], [88, 7, 5])[0]
        if status in ("Delivered", "Returned"):
            days = random.choices(range(1, 10), [8, 24, 26, 18, 10, 6, 4, 2, 2])[0]
            if tier in ("Gold", "Platinum"):
                days = max(1, days - 1)
            if status == "Delivered" and random.random() < 0.6:
                rating = random.choices([5, 4, 3, 2, 1], [45, 30, 13, 7, 5])[0]
                if days >= 6:
                    rating = max(1, rating - random.choice([1, 2]))
            elif status == "Returned" and random.random() < 0.4:
                rating = random.choice([1, 2, 3])
        rows.append((oid, c[0], d.isoformat(), wchoice(PAYMENTS), status, days, rating))
    return rows


def make_items(orders, customers, products):
    tier_of = {c[0]: c[5] for c in customers}
    pids = [p[0] for p in products]
    price = {p[0]: p[3] for p in products}
    popularity = [random.lognormvariate(0, 0.8) / price[p] ** 0.3 for p in pids]
    rows = []
    for oid, cid, odate, *_ in orders:
        n = random.choices([1, 2, 3, 4, 5], [50, 25, 14, 7, 4])[0]
        chosen = set()
        while len(chosen) < n:
            chosen.add(random.choices(pids, popularity)[0])
        for pid in chosen:
            qty = random.choices([1, 2, 3, 4], [60, 22, 12, 6])[0] if price[pid] < 60 else random.choices([1, 2], [92, 8])[0]
            disc = random.choices([0, 5, 10, 15, 20], DISCOUNT_WEIGHTS[tier_of[cid]])[0]
            if odate[5:7] in ("11", "12") and random.random() < 0.4:
                disc = max(disc, 15)
            sale_price = round(price[pid] * random.uniform(0.95, 1.05), 2)
            rows.append((oid, pid, qty, sale_price, float(disc)))
    return rows


def main():
    DB_PATH.unlink(missing_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)

    products, customers = make_products(), make_customers()
    orders = make_orders(customers)
    items = make_items(orders, customers, products)

    con.executemany("INSERT INTO categories VALUES (?, ?)", list(enumerate(CATEGORIES, start=1)))
    con.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)", customers)
    con.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)
    con.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", orders)
    con.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)
    con.commit()

    for t in ("categories", "customers", "products", "orders", "order_items"):
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    print("foreign key violations:", len(con.execute("PRAGMA foreign_key_check").fetchall()))
    con.close()


if __name__ == "__main__":
    main()
