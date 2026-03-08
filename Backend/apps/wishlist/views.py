from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttles import WishlistMutationRateThrottle

from .models import Wishlist
from .serializers import WishlistCreateSerializer, WishlistItemSerializer


class WishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "POST":
            return [WishlistMutationRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product').prefetch_related('product__images')

    def get(self, request):
        serializer = WishlistItemSerializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        create_serializer = WishlistCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        product = create_serializer.validated_data['product']
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        response_serializer = WishlistItemSerializer(wishlist_item)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WishlistDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "DELETE":
            return [WishlistMutationRateThrottle()]
        return super().get_throttles()

    def delete(self, request, product_id):
        deleted_count, _ = Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
        if deleted_count == 0:
            return Response({'detail': 'Wishlist item not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
