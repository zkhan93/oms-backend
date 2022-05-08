from rest_framework import serializers

from api.models import Customer, Item, Order, OrderItem, OrderState


class OrderSerializer(serializers.ModelSerializer):
    state = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        validated_data["state"] = OrderState.CREATED
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class CreateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ["price"]


class NestedOrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="item.name")
    item_id = serializers.IntegerField(source="item.id")

    class Meta:
        model = OrderItem
        exclude = ["item", "order"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = NestedOrderItemSerializer(source="orderitem_set", many=True)

    class Meta:
        model = Order
        exclude = []


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
