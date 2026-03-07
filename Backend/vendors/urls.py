from django.urls import path

from .views import (
    VendorDashboardEarningsView,
    VendorDashboardOrdersView,
    VendorDashboardProductView,
    VendorProfileView,
)

urlpatterns = [
    path("profile/", VendorProfileView.as_view(), name="vendor-profile"),
    path("dashboard/products/", VendorDashboardProductView.as_view(), name="vendor-dashboard-products"),
    path("dashboard/orders/", VendorDashboardOrdersView.as_view(), name="vendor-dashboard-orders"),
    path("dashboard/earnings/", VendorDashboardEarningsView.as_view(), name="vendor-dashboard-earnings"),
]
