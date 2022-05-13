import logging
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from api.models import Order, OrderItem, OrderState


class BaseTest(TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)
        self.username = "zkhan1093@gmail.com"
        self.client = APIClient()
        self.client.login(username=self.username, password="admin")
        return super().setUp()


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


class OrderItemTestCase(BaseTest):
    fixtures = ["fixtures/core.json"]

    def setUp(self) -> None:
        self.order = Order.objects.create(customer_id=1)
        return super().setUp()

    def test_order_item_add(self):
        url = reverse("order-add-item", args=(self.order.id,))
        data = {"name": "rice", "quantity": 10, "unit": "u"}
        self.assertEqual(self.order.orderitem_set.count(), 0)
        res = self.client.post(url, data)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.orderitem_set.count(), 1)

    def test_order_item_update(self):
        orderitem = OrderItem.objects.create(
            **{"order_id": self.order.id, "item_id": 1, "quantity": 10, "unit": "u"}
        )
        self.order.orderitem_set.add(orderitem)

        self.assertEqual(self.order.orderitem_set.first().quantity, 10)
        self.assertEqual(self.order.orderitem_set.first().unit, "u")

        url = reverse("orderitem-detail", args=(orderitem.id,))
        data = {"quantity": 11, "unit": "kg"}
        res = self.client.patch(url, data=data)
        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.orderitem_set.first().quantity, 11)
        self.assertEqual(self.order.orderitem_set.first().unit, "kg")

    def test_order_item_delete(self):
        orderitem = OrderItem.objects.create(
            **{"order_id": self.order.id, "item_id": 1, "quantity": 10, "unit": "u"}
        )
        self.order.orderitem_set.add(orderitem)

        self.assertEqual(self.order.orderitem_set.count(), 1)

        url = reverse("orderitem-detail", args=(orderitem.id,))
        res = self.client.delete(url)
        self.assertEquals(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.order.orderitem_set.count(), 0)
