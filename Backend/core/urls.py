from django.contrib import admin
from django.urls import include, path

from adminpanel.views import (
    AdminDeliverOrderView,
    AdminOrderDetailView,
    AdminOrderListView,
    AdminShipOrderView,
    AdminOrderStatusUpdateView,
    AnalyticsSummaryView,
)

urlpatterns = [
    path("admin/analytics/summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("admin/orders/", AdminOrderListView.as_view(), name="admin-orders-list"),
    path("admin/orders/<int:order_id>/", AdminOrderDetailView.as_view(), name="admin-orders-detail"),
    path("admin/orders/<int:order_id>/status/", AdminOrderStatusUpdateView.as_view(), name="admin-orders-status"),
    path("admin/orders/<int:order_id>/ship/", AdminShipOrderView.as_view(), name="admin-orders-ship"),
    path("admin/orders/<int:order_id>/deliver/", AdminDeliverOrderView.as_view(), name="admin-orders-deliver"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api_urls")),
]
