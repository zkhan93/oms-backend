from django.db import models
from django.contrib.auth.models import AbstractUser


class OrderState:
    CREATED = "C"
    PROCESSING = "P"
    DELIVERED = "D"
    CANCELLED = "X"


class User(AbstractUser):
    pass


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ship = models.CharField(max_length=50)
    supervisor = models.CharField(max_length=50)
    contact = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    state = models.CharField(
        max_length=1,
        choices=(
            (OrderState.CREATED, "Created"),
            (OrderState.PROCESSING, "Processing"),
            (OrderState.DELIVERED, "Delivered"),
            (OrderState.CANCELLED, "Cancelled"),
        ),
    )
    comment = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"


class Item(models.Model):
    name = models.CharField(max_length=100)
    default_price = models.DecimalField(max_digits=30, decimal_places=2)

    def __str__(self):
        return self.name


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    unit = models.CharField(
        max_length=10,
        choices=(
            ("u", "Unit"),
            ("dozen", "Dozen"),
            ("g", "Grams"),
            ("kg", "Kilogram"),
            ("lts", "Liters"),
            ("m", "Meters"),
            ("cm", "Centimeters"),
        ),
    )

    def __str__(self):
        return f"Order#{self.order.id} - {self.item.id}"
