import csv
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from emporio_agent.config import settings
from emporio_agent.db.schema import Category, Customer, Order, OrderItem, Product, Promotion

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite database ingestion from CSVs and provides typed queries."""

    def __init__(self, db_path: Path | str | None = None, data_dir: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else settings.DATABASE_PATH
        self.data_dir = Path(data_dir) if data_dir else settings.DATA_DIR
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _find_csv(self, keyword: str) -> Path:
        """Find CSV file by partial keyword in data directory."""
        for file in self.data_dir.glob("*.csv"):
            if keyword.lower() in file.name.lower():
                return file
        raise FileNotFoundError(f"Could not find CSV for '{keyword}' in {self.data_dir}")

    def _init_db(self, force_reload: bool = False) -> None:
        """Initialize SQLite tables and ingest CSVs if empty or force_reload is True."""
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist. Skipping CSV ingestion.")
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if tables already exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            if cursor.fetchone() and not force_reload:
                return

            logger.info("Initializing SQLite database and ingesting CSV records...")

            cursor.executescript("""
                DROP TABLE IF EXISTS categories;
                DROP TABLE IF EXISTS products;
                DROP TABLE IF EXISTS customers;
                DROP TABLE IF EXISTS orders;
                DROP TABLE IF EXISTS order_items;
                DROP TABLE IF EXISTS promotions;

                CREATE TABLE categories (
                    category_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT
                );

                CREATE TABLE products (
                    product_id INTEGER PRIMARY KEY,
                    price_brl REAL NOT NULL,
                    name TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    stock_quantity INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    specs TEXT,
                    created_at TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                );

                CREATE TABLE customers (
                    customer_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    city TEXT
                );

                CREATE TABLE orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_brl REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    tracking_code TEXT,
                    estimated_delivery TEXT,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                );

                CREATE TABLE order_items (
                    order_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id),
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                );

                CREATE TABLE promotions (
                    promotion_id INTEGER PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    discount_percent INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    is_active INTEGER NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                );

                CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
                CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
                CREATE INDEX IF NOT EXISTS idx_products_price ON products(price_brl);
                CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_code);
                CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
                CREATE INDEX IF NOT EXISTS idx_promotions_product ON promotions(product_id);
            """)

            # Ingest categories
            with open(self._find_csv("categories"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                cursor.executemany(
                    "INSERT INTO categories VALUES (:category_id, :name, :description)",
                    list(reader),
                )

            # Ingest products
            with open(self._find_csv("products"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                products_data = []
                for row in reader:
                    products_data.append({
                        "product_id": int(row["product_id"]),
                        "price_brl": float(row["price_brl"]),
                        "name": row["name"].strip(),
                        "category_id": int(row["category_id"]),
                        "description": row["description"].strip(),
                        "stock_quantity": int(row["stock_quantity"]),
                        "status": row["status"].strip(),
                        "specs": row.get("specs", "{}"),
                        "created_at": row.get("created_at", ""),
                    })
                cursor.executemany(
                    "INSERT INTO products VALUES (:product_id, :price_brl, :name, :category_id, :description, :stock_quantity, :status, :specs, :created_at)",
                    products_data,
                )

            # Ingest customers
            with open(self._find_csv("customers"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                cursor.executemany(
                    "INSERT INTO customers VALUES (:customer_id, :name, :phone, :email, :city)",
                    list(reader),
                )

            # Ingest orders
            with open(self._find_csv("orders"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                orders_data = []
                for row in reader:
                    orders_data.append({
                        "order_id": int(row["order_id"]),
                        "customer_id": int(row["customer_id"]),
                        "order_date": row["order_date"].strip(),
                        "status": row["status"].strip(),
                        "total_brl": float(row["total_brl"]),
                        "payment_method": row["payment_method"].strip(),
                        "tracking_code": row["tracking_code"].strip() if row.get("tracking_code") else None,
                        "estimated_delivery": row["estimated_delivery"].strip() if row.get("estimated_delivery") else None,
                        "notes": row["notes"].strip() if row.get("notes") else None,
                    })
                cursor.executemany(
                    "INSERT INTO orders VALUES (:order_id, :customer_id, :order_date, :status, :total_brl, :payment_method, :tracking_code, :estimated_delivery, :notes)",
                    orders_data,
                )

            # Ingest order_items
            with open(self._find_csv("order_items"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                items_data = [
                    {
                        "order_id": int(row["order_id"]),
                        "quantity": int(row["quantity"]),
                        "product_id": int(row["product_id"]),
                    }
                    for row in reader
                ]
                cursor.executemany(
                    "INSERT INTO order_items VALUES (:order_id, :quantity, :product_id)",
                    items_data,
                )

            # Ingest promotions
            with open(self._find_csv("promotions"), encoding="utf-8") as f:
                reader = csv.DictReader(f)
                promos_data = [
                    {
                        "promotion_id": int(row["promotion_id"]),
                        "product_id": int(row["product_id"]),
                        "discount_percent": int(row["discount_percent"]),
                        "description": row["description"].strip(),
                        "is_active": int(row["is_active"]),
                    }
                    for row in reader
                ]
                cursor.executemany(
                    "INSERT INTO promotions VALUES (:promotion_id, :product_id, :discount_percent, :description, :is_active)",
                    promos_data,
                )

            conn.commit()
            logger.info("Database ingestion successfully finished.")

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        raw_specs = row["specs"]
        specs_dict: Dict[str, Any] = {}
        if raw_specs:
            try:
                specs_dict = json.loads(raw_specs)
            except Exception:
                specs_dict = {"raw": raw_specs}

        active_discount = row["active_discount_percent"] if "active_discount_percent" in row.keys() else None
        price = float(row["price_brl"])
        promo_price = round(price * (1.0 - (active_discount / 100.0)), 2) if active_discount else None

        return Product(
            product_id=row["product_id"],
            name=row["name"],
            price_brl=price,
            category_id=row["category_id"],
            category_name=row["category_name"] if "category_name" in row.keys() else None,
            description=row["description"],
            stock_quantity=row["stock_quantity"],
            status=row["status"],
            specs=specs_dict,
            created_at=row["created_at"],
            active_discount_percent=active_discount,
            promotional_price=promo_price,
        )

    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        in_stock_only: bool = True,
        limit: int = 10,
    ) -> List[Product]:
        """Search products with fuzzy matching, price bounds, category, and active promotion checks."""
        sql = """
            SELECT p.*, c.name AS category_name, pr.discount_percent AS active_discount_percent
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
            WHERE 1=1
        """
        params: List[Any] = []

        if in_stock_only:
            sql += " AND p.stock_quantity > 0 AND p.status = 'active'"

        if query:
            sql += " AND (p.name LIKE ? OR p.description LIKE ? OR c.name LIKE ?)"
            term = f"%{query.strip()}%"
            params.extend([term, term, term])

        if category:
            sql += " AND c.name LIKE ?"
            params.append(f"%{category.strip()}%")

        if max_price is not None:
            sql += " AND p.price_brl <= ?"
            params.append(max_price)

        if min_price is not None:
            sql += " AND p.price_brl >= ?"
            params.append(min_price)

        sql += " ORDER BY p.price_brl ASC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self._row_to_product(row) for row in cursor.fetchall()]

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Retrieve a specific product by its ID."""
        sql = """
            SELECT p.*, c.name AS category_name, pr.discount_percent AS active_discount_percent
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
            WHERE p.product_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (product_id,))
            row = cursor.fetchone()
            return self._row_to_product(row) if row else None

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Retrieve a product by partial or exact name match."""
        sql = """
            SELECT p.*, c.name AS category_name, pr.discount_percent AS active_discount_percent
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
            WHERE p.name LIKE ?
            LIMIT 1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (f"%{name.strip()}%",))
            row = cursor.fetchone()
            return self._row_to_product(row) if row else None

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Retrieve order details including customer info and item list."""
        sql = """
            SELECT o.*, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (order_id,))
            order_row = cursor.fetchone()
            if not order_row:
                return None

            # Fetch order items
            cursor.execute("""
                SELECT oi.order_id, oi.product_id, oi.quantity, p.name AS product_name, p.price_brl AS unit_price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = [
                OrderItem(
                    order_id=row["order_id"],
                    product_id=row["product_id"],
                    quantity=row["quantity"],
                    product_name=row["product_name"],
                    unit_price=float(row["unit_price"]),
                )
                for row in cursor.fetchall()
            ]

            return Order(
                order_id=order_row["order_id"],
                customer_id=order_row["customer_id"],
                customer_name=order_row["customer_name"],
                customer_phone=order_row["customer_phone"],
                customer_email=order_row["customer_email"],
                order_date=order_row["order_date"],
                status=order_row["status"],
                total_brl=float(order_row["total_brl"]),
                payment_method=order_row["payment_method"],
                tracking_code=order_row["tracking_code"],
                estimated_delivery=order_row["estimated_delivery"],
                notes=order_row["notes"],
                items=items,
            )

    def get_order_by_tracking(self, tracking_code: str) -> Optional[Order]:
        """Retrieve order by tracking code (e.g. BR4K7M2X9P1BR)."""
        sql = "SELECT order_id FROM orders WHERE UPPER(tracking_code) = UPPER(?)"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (tracking_code.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self.get_order_by_id(row["order_id"])

    def get_customer_orders(self, query: str) -> List[Order]:
        """Find orders by customer name, email, or phone."""
        sql = """
            SELECT o.order_id
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE c.name LIKE ? OR c.email LIKE ? OR c.phone LIKE ?
            ORDER BY o.order_date DESC
        """
        term = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (term, term, term))
            order_ids = [row["order_id"] for row in cursor.fetchall()]
            return [order for oid in order_ids if (order := self.get_order_by_id(oid)) is not None]

    def get_active_promotions(self) -> List[Promotion]:
        """Retrieve all currently active promotions."""
        sql = """
            SELECT pr.*, p.name AS product_name
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
            WHERE pr.is_active = 1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [
                Promotion(
                    promotion_id=row["promotion_id"],
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    discount_percent=row["discount_percent"],
                    description=row["description"],
                    is_active=bool(row["is_active"]),
                )
                for row in cursor.fetchall()
            ]

    def get_product_promotions_history(self, product_id: int) -> List[Promotion]:
        """Get all promotions associated with a product (active or expired)."""
        sql = """
            SELECT pr.*, p.name AS product_name
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
            WHERE pr.product_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (product_id,))
            return [
                Promotion(
                    promotion_id=row["promotion_id"],
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    discount_percent=row["discount_percent"],
                    description=row["description"],
                    is_active=bool(row["is_active"]),
                )
                for row in cursor.fetchall()
            ]
