import logging
from multiprocessing import context
from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from api.models import Customer, Item, Order, OrderItem
from api.serializers import (
    CreateCustomerSerializer,
    CreateOrderItemSerializer,
    OrderCreateSerializer,
    DetailCustomerSerializer,
    ItemSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


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
        if self.action in ("list",):
            return OrderListSerializer
        if self.action in ("create",):
            return OrderCreateSerializer
        return OrderDetailSerializer

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
        order = self.get_object()
        serializer = CreateOrderItemSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.validated_data["order"] = order
            serializer.create(serializer.validated_data)
        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def partial_update(self, request, *args, **kwargs):
        logging.info(f"{args}, {kwargs}")
        logging.info(request.data)
        return super().partial_update(request, *args, **kwargs)

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCustomerSerializer
        return DetailCustomerSerializer


class ItemsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
