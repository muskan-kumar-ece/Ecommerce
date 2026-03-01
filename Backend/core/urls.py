from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/orders/", include("orders.urls")),
]
