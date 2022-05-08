import logging
from django.urls import include, path
from rest_framework import routers
from api import views
from pprint import pformat

router = routers.DefaultRouter()
router.register(r"customer", views.CustomerViewSet)
router.register(r"order", views.OrderViewSet)
router.register(r"item", views.ItemsViewSet)
router.register(r"orderitem", views.OrderItemViewSet)

logging.debug(pformat(router.urls))
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
