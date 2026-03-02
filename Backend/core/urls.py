from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", include("adminpanel.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api_urls")),
]
