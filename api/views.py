from decimal import Decimal
import logging
from django.http import FileResponse
from django.template import loader
import pdfkit
import tempfile

from rest_framework import mixins, permissions, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Customer, Item, Order, OrderItem
from api.serializers import (
    CreateCustomerSerializer,
    CreateOrderItemSerializer,
    DetailCustomerSerializer,
    ItemSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderSerializer,
    UpdateOrderItemSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        logging.info(request.data)
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        roles = [g.name for g in user.groups.all()]
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "customer_id": user.customer.id,
                "roles": roles,
            }
        )


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "all":
            return request.user.groups.filter(name="admin").exists()
        return True

    def has_object_permission(self, request, view, obj):
        customer = getattr(request.user, "customer", None)
        return (
            obj.customer == customer
            or request.user.groups.filter(name="admin").exists()
        )


class IsOrderItemOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        customer = getattr(request.user, "customer", None)
        return (
            obj.order.customer == customer
            or request.user.groups.filter(name="admin").exists()
        )


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action in ("list", "all"):
            return OrderListSerializer
        if self.action in ("create",):
            return OrderCreateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        if self.action == "all":
            return Order.objects.all().order_by("-created_on")
        user = self.request.user
        if self.action == "list":
            try:
                customer = Customer.objects.get(user=user)
            except Customer.DoesNotExist:
                return Order.objects.none()
            else:
                return Order.objects.filter(customer=customer).order_by("-created_on")
        return Order.objects.order_by("-created_on")

    @action(detail=False, methods=["get"])
    def all(self, request, *args, **kwargs):

        return self.list(self, request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk):
        order = self.get_object()
        serializer = CreateOrderItemSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.validated_data["order"] = order
            serializer.create(serializer.validated_data)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk):
        order = self.get_object()
        serializer = OrderDetailSerializer(instance=order)
        context = serializer.data
        for item in context["items"]:
            logging.info(item)
            if item["price"]:
                item["total"] = Decimal(
                    Decimal(item["price"]) * Decimal(item["quantity"])
                )
            else:
                item["total"] = ""
        template = loader.get_template("api/receipt.html")
        html_content = template.render(context, request)
        logging.info(html_content)
        # TODO: change receipt_filename to some media location
        receipt_filename = f"order_{order.id}.pdf"
        html_file = tempfile.NamedTemporaryFile("w", suffix=".html")
        html_file.write(html_content)
        html_file.flush()
        logging.info(html_file.name)
        pdfkit.from_file(html_file.name, receipt_filename)
        html_file.close()

        response = FileResponse(
            open(receipt_filename, "rb"), content_type="application/pdf"
        )
        # response["Content-Disposition"] = f'attachment; filename="{receipt_filename}"'
        return response

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def partial_update(self, request, *args, **kwargs):
        logging.info(f"{args}, {kwargs}")
        logging.info(request.data)
        return super().partial_update(request, *args, **kwargs)


class OrderItemViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = OrderItem.objects.all()
    serializer_class = UpdateOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderItemOwnerOrAdmin]


class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Customer.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [
                permissions.AllowAny(),
            ]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCustomerSerializer
        return DetailCustomerSerializer


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="admin").exists()


class ItemsViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAdmin]
