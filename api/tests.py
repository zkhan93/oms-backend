import logging
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from api.models import Order, OrderItem, OrderState, User


class BaseTest(TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)
        self.username = "1111111111"
        self.client = APIClient()
        self.client.login(username=self.username, password="admin")
        return super().setUp()


class CustomerTestCase(TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)
        self.client = APIClient()
        return super().setUp()

    def test_create_customer(self):
        url = reverse("customer-list")
        data = {
            "ship": "Ship1",
            "supervisor": "Raju",
            "contact": "8932061116",
            "password": "1234",
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        res = self.client.post(url, data)
        # contact already registered
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_auth_token(self):
        url = reverse("customer-list")
        data = {
            "ship": "Ship1",
            "supervisor": "Raju",
            "contact": "8932061116",
            "password": "1234",
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)

        res = self.client.post(
            "/api-auth/", {"username": "8932061116", "password": "1234"}
        )
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(pk=1)
        user.is_active = True
        user.save()

        res = self.client.post(
            "/api-auth/", {"username": "8932061116", "password": "1234"}
        )
        self.assertEquals(res.status_code, status.HTTP_200_OK)


class OrderTestCase(BaseTest):
    fixtures = ["fixtures/core.json"]

    def test_order_create_with_no_items(self):
        url = reverse("order-list")
        data = {
            "items": [],
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", res.json())

    def test_order_create_without_customer(self):
        url = reverse("order-list")
        data = {
            "items": [{"name": "rice", "quantity": 1, "unit": "kg"}],
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertDictContainsSubset(
            {"username": self.username}, res.json()["customer"]
        )

    def test_order_create_ok(self):
        url = reverse("order-list")
        data = {
            "items": [
                {
                    "id": 1,
                    "name": "rice",
                    "quantity": 1,
                    "unit": "kg",
                }
            ]
        }
        res = self.client.post(
            url,
            data,
        )
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertDictContainsSubset(data, res.json())

    def test_order_create_state_no_effect(self):
        url = reverse("order-list")
        data = {
            "items": [
                {
                    "name": "rice",
                    "quantity": 1,
                    "unit": "kg",
                }
            ],
            "state": OrderState.DELIVERED,
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertEquals(res.json()["state"], OrderState.CREATED)


class OrderAdminTestCase(BaseTest):
    fixtures = ["fixtures/core.json", "fixtures/admin2.json", "fixtures/customer3.json"]

    def setUp(self) -> None:
        super().setUp()
        # create order from admin1
        url = reverse("order-list")
        data = {
            "items": [{"name": "rice", "quantity": 1, "unit": "kg"}],
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        # login with admin2
        self.username = "2222222222"
        self.client.login(username=self.username, password="admin")

    def test_orders_visible_to_all_admin(self):
        url = reverse("order-all")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEquals(len(res.json()["results"]), 1)

    def test_orders_not_visible_to_other_customer(self):
        self.client.login(username="3333333333", password="admin")
        url = reverse("order-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEquals(len(res.json()["results"]), 0)

    def test_orders_all_unauthorized(self):
        self.client.login(username="3333333333", password="admin")
        url = reverse("order-all")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class OrderItemTestCase(BaseTest):
    fixtures = ["fixtures/core.json"]

    def setUp(self) -> None:
        self.order = Order.objects.create(customer_id=1)
        return super().setUp()

    def test_order_item_add(self):
        url = reverse("order-add-item", args=(self.order.id,))
        data = {"name": "rice", "quantity": 10, "unit": "number"}

        self.assertEqual(self.order.orderitem_set.count(), 0)
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.orderitem_set.count(), 1)

    def test_order_item_update(self):
        orderitem = OrderItem.objects.create(
            **{
                "order_id": self.order.id,
                "item_id": 1,
                "quantity": 10,
                "unit": "number",
            }
        )
        self.order.orderitem_set.add(orderitem)

        self.assertEqual(self.order.orderitem_set.first().quantity, 10)
        self.assertEqual(self.order.orderitem_set.first().unit, "number")

        url = reverse("orderitem-detail", args=(orderitem.id,))
        data = {"quantity": 11, "unit": "kg"}
        res = self.client.patch(url, data=data)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.orderitem_set.first().quantity, 11)
        self.assertEqual(self.order.orderitem_set.first().unit, "kg")

    def test_order_item_delete(self):
        orderitem = OrderItem.objects.create(
            **{
                "order_id": self.order.id,
                "item_id": 1,
                "quantity": 10,
                "unit": "number",
            }
        )
        self.order.orderitem_set.add(orderitem)

        self.assertEqual(self.order.orderitem_set.count(), 1)

        url = reverse("orderitem-detail", args=(orderitem.id,))
        res = self.client.delete(url)
        self.assertEquals(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.order.orderitem_set.count(), 0)


class ItemTestCase(BaseTest):
    fixtures = ["fixtures/core.json", "fixtures/customer3.json"]

    def test_item_list_admin_can_access(self):
        url = reverse("item-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_item_list_customer_cannot_access(self):
        self.client.login(username="3333333333", password="admin")
        url = reverse("item-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_item_update_customer_cannot_access(self):
        self.client.login(username="3333333333", password="admin")
        url = reverse("item-detail", args=(1,))
        res = self.client.patch(url, data={"default_price": 200})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
