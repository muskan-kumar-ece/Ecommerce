from django.urls import include, path
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from orders.views import AdminAnalyticsView
from products.views import ProductSearchSuggestionsView, ProductSearchView


class AuthTokenThrottle(AnonRateThrottle):
    """Strict rate limit on login and token-refresh endpoints to prevent brute-force attacks.

    Inherits AnonRateThrottle so the limit is keyed by IP address (not user identity),
    which is appropriate here because the client may not yet be authenticated (login)
    or is rotating its token (refresh). The 'auth' scope defaults to 10/minute and
    can be overridden via the THROTTLE_RATE_AUTH environment variable.
    """

    scope = "auth"


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AuthTokenThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthTokenThrottle]


urlpatterns = [
    path("auth/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", ThrottledTokenRefreshView.as_view(), name="token_refresh"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("search/", ProductSearchView.as_view(), name="product-search"),
    path("search", ProductSearchView.as_view(), name="product-search-no-slash"),
    path("search/suggestions/", ProductSearchSuggestionsView.as_view(), name="product-search-suggestions"),
    path("search/suggestions", ProductSearchSuggestionsView.as_view(), name="product-search-suggestions-no-slash"),
    path("users/", include("users.urls")),
    path("products/", include("products.urls")),
    path("flash-sales/", include("products.flash_sale_urls")),
    path("reviews/", include("products.review_urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
    path("chatbot/", include("apps.chatbot.urls")),
    path("price-watch/", include("apps.price_watch.urls")),
    path("vendors/", include("vendors.urls")),
]
