from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from api.models import Order, OrderItem, OrderState


class OrderTestCase(TestCase):
    fixtures = ["fixtures/core.json"]

    def setUp(self) -> None:
        self.client = Client()
        self.client.login(username="zkhan1093@gmail.com", password="admin")
        return super().setUp()

    def test_order_create_ok(self):
        url = reverse("order-list")
        data = {
            "customer": 1,
        }
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)

    def test_order_create_state_no_effect(self):
        url = reverse("order-list")
        data = {"customer": 1, "state": OrderState.DELIVERED}
        res = self.client.post(url, data)
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertEquals(res.json()["state"], OrderState.CREATED)


class OrderItemTestCase(TestCase):
    fixtures = ["fixtures/core.json"]

    def setUp(self) -> None:
        self.client = Client()
        self.client.login(username="zkhan1093@gmail.com", password="admin")
        self.order = Order.objects.create(customer_id=1)
        return super().setUp()

    def test_order_item_add(self):

        url = reverse("order-add-item", args=(self.order.id,))
        data = {"order": self.order.id, "item": 1, "quantity": 10, "unit": "u"}
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
        res = self.client.patch(url, data=data, content_type="application/json")
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
