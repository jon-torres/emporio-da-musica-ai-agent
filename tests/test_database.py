import pytest
from emporio_agent.db.database import Database


@pytest.fixture
def db(tmp_path):
    # Use temporary DB path so tests don't pollute local file, but use real CSV data
    test_db_path = tmp_path / "test_emporio.db"
    return Database(db_path=test_db_path)


def test_search_violao_under_1000(db):
    results = db.search_products(query="violão", max_price=1000.0, in_stock_only=True)
    assert len(results) > 0
    for product in results:
        assert product.price_brl <= 1000.0
        assert product.stock_quantity > 0
        assert "violão" in product.name.lower() or "violão" in product.description.lower() or product.category_id == 5


def test_get_product_takamine_gd20(db):
    product = db.get_product_by_name("Takamine GD20")
    assert product is not None
    assert "Takamine GD20" in product.name
    assert product.price_brl == 2199.0
    assert product.category_name == "Violões"
    assert product.specs.get("top") == "Cedro Sólido"

    # Verify promo history (it had an expired promotion)
    promos = db.get_product_promotions_history(product.product_id)
    assert len(promos) > 0
    assert any(p.description == "Oferta Especial" and not p.is_active for p in promos)


def test_get_order_by_tracking_code(db):
    tracking = "BRQM7890123BR"
    order = db.get_order_by_tracking(tracking)
    assert order is not None
    assert order.order_id == 4
    assert order.customer_name == "Lucas Mendes da Silva"
    assert order.status == "delivered"
    assert len(order.items) > 0


def test_get_customer_orders(db):
    orders = db.get_customer_orders("Lucas Mendes")
    assert len(orders) >= 1
    assert any(o.customer_name == "Lucas Mendes da Silva" for o in orders)


def test_active_promotions(db):
    active_promos = db.get_active_promotions()
    assert len(active_promos) > 0
    for promo in active_promos:
        assert promo.is_active is True
        assert promo.discount_percent > 0
