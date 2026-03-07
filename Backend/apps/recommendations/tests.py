from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from orders.models import Order, OrderItem
from products.models import Category, Product

from .services import get_similar_products, get_trending_products, get_user_recommendations


class RecommendationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="******",
            name="Buyer",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="******",
            name="Other",
        )
        self.category_a = Category.objects.create(name="Laptops")
        self.category_b = Category.objects.create(name="Accessories")

    def _create_product(self, name, category, sku, price="1000.00", is_active=True):
        return Product.objects.create(
            name=name,
            category=category,
            description=f"{name} description",
            price=Decimal(price),
            sku=sku,
            stock_quantity=100,
            is_active=is_active,
        )

    def _create_paid_order_item(self, user, product, quantity=1):
        order = Order.objects.create(
            user=user,
            total_amount=product.price * quantity,
            payment_status=Order.PaymentStatus.PAID,
            status=Order.Status.CONFIRMED,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )

    def test_get_similar_products_returns_same_category_excluding_source(self):
        source = self._create_product("Laptop A", self.category_a, "SKU-A")
        similar = self._create_product("Laptop B", self.category_a, "SKU-B")
        different = self._create_product("Mouse", self.category_b, "SKU-C")

        self._create_paid_order_item(self.user, similar)
        self._create_paid_order_item(self.user, different)

        result_ids = list(get_similar_products(source.id).values_list("id", flat=True))

        self.assertIn(similar.id, result_ids)
        self.assertNotIn(source.id, result_ids)
        self.assertNotIn(different.id, result_ids)

    def test_get_user_recommendations_uses_purchase_history_and_excludes_purchased(self):
        purchased = self._create_product("Laptop A", self.category_a, "SKU-D")
        recommended = self._create_product("Laptop B", self.category_a, "SKU-E")
        other_category = self._create_product("Mouse", self.category_b, "SKU-F")

        self._create_paid_order_item(self.user, purchased)
        self._create_paid_order_item(self.other_user, recommended)
        self._create_paid_order_item(self.other_user, other_category)

        result_ids = list(get_user_recommendations(self.user.id).values_list("id", flat=True))

        self.assertIn(recommended.id, result_ids)
        self.assertNotIn(purchased.id, result_ids)
        self.assertNotIn(other_category.id, result_ids)

    def test_get_user_recommendations_falls_back_to_trending_when_no_purchase_history(self):
        trending_product = self._create_product("Popular Laptop", self.category_a, "SKU-G")
        self._create_paid_order_item(self.other_user, trending_product)

        result_ids = list(get_user_recommendations(self.user.id).values_list("id", flat=True))

        self.assertEqual(result_ids, [trending_product.id])

    def test_get_trending_products_orders_by_order_count_and_limits_to_ten(self):
        products = [
            self._create_product(f"Product {index}", self.category_a, f"SKU-T-{index}")
            for index in range(12)
        ]

        for index, product in enumerate(products):
            for _ in range(index + 1):
                self._create_paid_order_item(self.other_user, product)

        trending = list(get_trending_products())

        self.assertEqual(len(trending), 10)
        self.assertEqual(trending[0].id, products[-1].id)
