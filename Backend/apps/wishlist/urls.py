from django.urls import path

from .views import WishlistDeleteView, WishlistView

urlpatterns = [
    path('', WishlistView.as_view(), name='wishlist-list-create'),
    path('<int:product_id>/', WishlistDeleteView.as_view(), name='wishlist-delete'),
]
