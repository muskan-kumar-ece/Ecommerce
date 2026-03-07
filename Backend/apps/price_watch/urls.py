from django.urls import path

from .views import PriceWatchDeleteView, PriceWatchView

urlpatterns = [
    path("", PriceWatchView.as_view(), name="price-watch-list-create"),
    path("<int:product_id>/", PriceWatchDeleteView.as_view(), name="price-watch-delete"),
]
