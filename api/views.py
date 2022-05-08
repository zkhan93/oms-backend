from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Customer, Item, Order, OrderItem
from api.serializers import (
    CreateOrderItemSerializer,
    ItemSerializer,
    OrderDetailSerializer,
    OrderSerializer,
    CustomerSerializer,
)


class IsOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        customer = getattr(request.user, "customer", None)
        return obj.customer == customer


class IsOrderItemOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        customer = getattr(request.user, "customer", None)
        return obj.order.customer == customer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]

    def get_serializer_class(self):
        if self.action in ("retrieve"):
            return OrderDetailSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            return Order.objects.none()
        else:
            return Order.objects.filter(customer=customer).order_by("-created_on")

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk):
        self.get_object()
        serializer = CreateOrderItemSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.create(serializer.validated_data)
        return Response(serializer.data)


class OrderItemViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = OrderItem.objects.all()
    serializer_class = CreateOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderItemOwner]


class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class ItemsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
