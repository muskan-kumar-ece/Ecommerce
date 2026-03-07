from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PriceWatch
from .serializers import PriceWatchCreateSerializer, PriceWatchItemSerializer
from .services import add_price_watch


class PriceWatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PriceWatch.objects.filter(user=self.request.user).select_related("product")

    def get(self, request):
        serializer = PriceWatchItemSerializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PriceWatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        watch, created = add_price_watch(user=request.user, product=serializer.validated_data["product"])
        response_serializer = PriceWatchItemSerializer(watch)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PriceWatchDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        deleted_count, _ = PriceWatch.objects.filter(user=request.user, product_id=product_id).delete()
        if deleted_count == 0:
            return Response({"detail": "Price watch item not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
