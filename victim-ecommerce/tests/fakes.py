from contextlib import asynccontextmanager
from datetime import datetime

import asyncpg


class Record(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


class FakeStore:
    def __init__(self):
        self.users = [
            Record(id=1, username="admin", email="admin@store.com", password="admin", role="admin", created_at=datetime(2026, 1, 1)),
            Record(id=2, username="user1", email="user1@store.com", password="password123", role="customer", created_at=datetime(2026, 1, 1)),
        ]
        self.products = [
            Record(id=1, name="Laptop Pro 15", description="High-performance laptop", price=1299.99, image_url=None, category="electronics", stock=10),
            Record(id=2, name="Classic T-Shirt", description="Cotton t-shirt", price=24.99, image_url=None, category="clothing", stock=5),
        ]
        self.reviews = [
            Record(id=1, product_id=1, user_id=2, rating=5, comment="Great", created_at=datetime(2026, 1, 2)),
        ]
        self.carts = {}  # user_id -> {product_id: qty}
        self.orders = []
        self.order_items = []
        self.next_user = 3
        self.next_review = 2
        self.next_order = 1
        self.fail_next_order_item = False


class FakeConn:
    def __init__(self, store: FakeStore):
        self.store = store
        self._in_tx = False

    def transaction(self):
        conn = self

        class Tx:
            async def __aenter__(self_inner):
                conn._in_tx = True
                return self_inner

            async def __aexit__(self_inner, exc_type, exc, tb):
                conn._in_tx = False
                return False

        return Tx()

    async def fetchrow(self, query, *args):
        sql = " ".join(query.split()).lower().replace(" = ", "=")
        if "insert into users" in sql:
            username, email, password = args
            if any(u["username"] == username or u["email"] == email for u in self.store.users):
                raise asyncpg.UniqueViolationError()
            user = Record(
                id=self.store.next_user,
                username=username,
                email=email,
                password=password,
                role="customer",
                created_at=datetime.utcnow(),
            )
            self.store.next_user += 1
            self.store.users.append(user)
            return user
        if "from users where username=" in sql.replace(" ", "") or (
            "from users where username=$1" in sql
        ):
            username, password = args
            for user in self.store.users:
                if user["username"] == username and user["password"] == password:
                    return user
            return None
        if "select id, username, email, role from users where username=$1" in sql:
            username, password = args
            for user in self.store.users:
                if user["username"] == username and user["password"] == password:
                    return user
            return None
        if "from products where id=$1" in sql and "insert" not in sql:
            product_id = args[0]
            return next((p for p in self.store.products if p["id"] == product_id), None)
        if "insert into orders" in sql:
            user_id, total, address = args
            order = Record(
                id=self.store.next_order,
                user_id=user_id,
                total=total,
                status="pending",
                shipping_address=address,
                created_at=datetime.utcnow(),
            )
            self.store.next_order += 1
            self.store.orders.append(order)
            return order
        if "insert into reviews" in sql:
            product_id, user_id, rating, comment = args
            review = Record(
                id=self.store.next_review,
                product_id=product_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
                created_at=datetime.utcnow(),
            )
            self.store.next_review += 1
            self.store.reviews.append(review)
            return review
        if "from orders where id=$1 and user_id=$2" in sql:
            order_id, user_id = args
            return next(
                (o for o in self.store.orders if o["id"] == order_id and o["user_id"] == user_id),
                None,
            )
        if "from users where id=$1" in sql:
            user_id = args[0]
            return next((u for u in self.store.users if u["id"] == user_id), None)
        if "from products where id =" in sql:
            # VULN path interpolates; tests use parameterized safe mode
            return None
        return None

    async def fetchval(self, query, *args):
        sql = " ".join(query.split()).lower().replace(" = ", "=")
        if "from cart_items where user_id=$1 and product_id=$2" in sql:
            user_id, product_id = args
            return self.store.carts.get(user_id, {}).get(product_id)
        if "from products where id=$1" in sql:
            product_id = args[0]
            return 1 if any(p["id"] == product_id for p in self.store.products) else None
        return None

    async def fetch(self, query, *args):
        sql = " ".join(query.split()).lower().replace(" = ", "=")
        if "from cart_items c" in sql and "for update" in sql:
            user_id = args[0]
            cart = self.store.carts.get(user_id, {})
            rows = []
            for pid, qty in cart.items():
                product = next(p for p in self.store.products if p["id"] == pid)
                rows.append(
                    Record(
                        product_id=pid,
                        quantity=qty,
                        price=product["price"],
                        name=product["name"],
                        stock=product["stock"],
                    )
                )
            return rows
        if "from cart_items c" in sql:
            user_id = args[0]
            cart = self.store.carts.get(user_id, {})
            rows = []
            for pid, qty in cart.items():
                product = next((p for p in self.store.products if p["id"] == pid), None)
                if product:
                    rows.append(Record(product_id=pid, quantity=qty, name=product["name"], price=product["price"]))
            return rows
        if "from products where category=$1" in sql:
            category, _limit, _offset = args
            return [p for p in self.store.products if p["category"] == category]
        if "from products order by id" in sql:
            return list(self.store.products)
        if "distinct category" in sql:
            return [Record(category=c) for c in sorted({p["category"] for p in self.store.products})]
        if "from products where name ilike" in sql:
            needle = args[0].replace("%", "").lower()
            return [p for p in self.store.products if needle in p["name"].lower() or needle in p["description"].lower()]
        if "from reviews where product_id=$1" in sql:
            product_id = args[0]
            return [r for r in self.store.reviews if r["product_id"] == product_id]
        if "from orders where user_id=$1" in sql:
            user_id = args[0]
            return [o for o in self.store.orders if o["user_id"] == user_id]
        if "from order_items" in sql:
            order_id = args[0]
            rows = []
            for item in self.store.order_items:
                if item["order_id"] == order_id:
                    product = next(p for p in self.store.products if p["id"] == item["product_id"])
                    rows.append(
                        Record(
                            product_id=item["product_id"],
                            quantity=item["quantity"],
                            price=item["price"],
                            name=product["name"],
                        )
                    )
            return rows
        return []

    async def execute(self, query, *args):
        sql = " ".join(query.split()).lower().replace(" = ", "=")
        if "insert into cart_items" in sql:
            user_id, product_id, qty = args
            cart = self.store.carts.setdefault(user_id, {})
            cart[product_id] = cart.get(product_id, 0) + qty
            return "INSERT 1"
        if "insert into order_items" in sql:
            if self.store.fail_next_order_item:
                self.store.fail_next_order_item = False
                raise RuntimeError("simulated order_items failure")
            order_id, product_id, quantity, price = args
            self.store.order_items.append(
                Record(order_id=order_id, product_id=product_id, quantity=quantity, price=price)
            )
            return "INSERT 1"
        if "delete from cart_items where user_id=$1 and product_id=$2" in sql:
            user_id, product_id = args
            cart = self.store.carts.get(user_id, {})
            if product_id not in cart:
                return "DELETE 0"
            del cart[product_id]
            return "DELETE 1"
        if "delete from cart_items where user_id=$1" in sql:
            user_id = args[0]
            self.store.carts.pop(user_id, None)
            return "DELETE 1"
        if "update products set stock" in sql:
            quantity, product_id = args
            product = next((p for p in self.store.products if p["id"] == product_id), None)
            if product:
                product["stock"] = product["stock"] - quantity
            return "UPDATE 1"
        return "OK"


class FakePool:
    def __init__(self, store: FakeStore):
        self.store = store

    def acquire(self):
        store = self.store

        @asynccontextmanager
        async def _acquire():
            yield FakeConn(store)

        return _acquire()
