import logging
from rest_framework import serializers
from django.db.models import Sum
from api.models import Customer, Item, Order, OrderItem, OrderState, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["groups"]


class CreateCustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(source="user.password", write_only=True)
    ship = serializers.CharField()
    supervisor = serializers.CharField()
    contact = serializers.CharField()
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "password", "ship", "supervisor", "contact", "username"]

    def validate_contact(self, contact):
        if User.objects.filter(username=contact).exists():
            raise serializers.ValidationError("Number already registered")
        return contact

    def create(self, validated_data):
        username = validated_data["contact"]
        password = validated_data.pop("user").get("password")
        user = User.objects.create_user(
            username=username, is_active=False, password=password
        )
        validated_data["user"] = user
        return super().create(validated_data)


class DetailCustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name")
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Customer
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    state = serializers.CharField(read_only=True)
    customer = DetailCustomerSerializer()

    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        validated_data["state"] = OrderState.CREATED
        return super().create(validated_data)


class OrderListSerializer(serializers.ModelSerializer):
    state = serializers.CharField(read_only=True)
    customer = DetailCustomerSerializer()
    item_count = serializers.IntegerField(source="orderitem_set.count")

    class Meta:
        model = Order
        fields = "__all__"

    def to_representation(self, instance):
        json_data = super().to_representation(instance)
        json_data["state"] = OrderState.values[json_data["state"]]
        return json_data


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class CreateOrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="item.name")

    class Meta:
        model = OrderItem
        fields = ["id", "name", "quantity", "unit"]

    def validate_name(self, name):
        return name and name.strip().lower()

    def create(self, validated_data):
        item = validated_data.pop("item")
        validated_data["item"], _ = Item.objects.get_or_create(**item)
        return super().create(validated_data)


class UpdateOrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="item.name")
    quantity = serializers.FloatField()
    unit = serializers.CharField()

    class Meta:
        model = OrderItem
        fields = ["id", "name", "quantity", "unit", "price"]

    def update(self, instance, validated_data):
        order_item = super().update(instance, validated_data)

        order = order_item.order
        order.total = order.orderitem_set.aggregate(total=Sum("price"))["total"]
        order.save()

        return order_item


class OrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    items = CreateOrderItemSerializer(many=True, source="orderitem_set")
    customer = DetailCustomerSerializer(read_only=True)
    item_count = serializers.IntegerField(source="orderitem_set.count", read_only=True)
    state = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "items",
            "customer",
            "item_count",
            "state",
            "comment",
            "created_on",
            "id",
        ]

    def validate_items(self, items):
        if not items or not len(items):
            raise serializers.ValidationError(
                "At least one item is required to create an order"
            )
        return items

    def create(self, validated_data):
        user = self.context["user"]
        validated_data["state"] = OrderState.CREATED
        validated_data["customer_id"] = Customer.objects.get(user=user).id
        orderitems = validated_data.pop("orderitem_set")
        order = super().create(validated_data)
        for orderitem in orderitems:
            orderitem["order"] = order
            CreateOrderItemSerializer().create(orderitem)
        return order


class NestedOrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="item.name")
    item_id = serializers.IntegerField(source="item.id")

    class Meta:
        model = OrderItem
        exclude = ["item", "order"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = NestedOrderItemSerializer(source="orderitem_set", many=True)
    customer = DetailCustomerSerializer()

    class Meta:
        model = Order
        fields = ["id", "customer", "state", "comment", "created_on", "items", "total"]

    def to_representation(self, instance):
        json_data = super().to_representation(instance)
        json_data["state"] = OrderState.values[json_data["state"]]
        return json_data

    def update(self, instance, validated_data):
        if (
            instance.state != OrderState.CANCELLED
            and validated_data["state"] == OrderState.CANCELLED
        ):
            validated_data[
                "comment"
            ] = f"Cancelled by - {self.context['user'].username}"
        logging.info(validated_data)
        return super().update(instance, validated_data)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"
