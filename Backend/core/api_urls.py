from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from orders.views import AdminAnalyticsView
from products.views import ProductSearchSuggestionsView, ProductSearchView

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
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
]
