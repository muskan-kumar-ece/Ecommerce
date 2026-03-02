from django.contrib import admin
from django.urls import include, path

from adminpanel.views import AnalyticsSummaryView

urlpatterns = [
    path("admin/analytics/summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api_urls")),
]
