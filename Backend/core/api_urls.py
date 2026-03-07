from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from orders.views import AdminAnalyticsView

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("users/", include("users.urls")),
    path("products/", include("products.urls")),
    path("reviews/", include("products.review_urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
]
