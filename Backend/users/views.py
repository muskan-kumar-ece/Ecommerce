from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttles import RegisterRateThrottle
from orders.models import Coupon

from .models import Referral
from .serializers import ReferralSummarySerializer, RegisterUserSerializer


class RegisterUserView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterUserSerializer
    throttle_classes = [RegisterRateThrottle]


class ReferralSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def get(self, request):
        referral_stats = Referral.objects.filter(referrer=request.user).aggregate(
            total_referrals=Count("id"),
            successful_referrals=Count("id", filter=Q(reward_issued=True)),
            pending_rewards=Count("id", filter=Q(reward_issued=False)),
        )
        earned_rewards = Coupon.objects.filter(eligible_user=request.user, code__startswith="REF").aggregate(
            total=Coalesce(
                Sum("discount_value"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]
        reward_coupon_codes = list(
            Coupon.objects.filter(eligible_user=request.user, code__startswith="REF")
            .order_by("-created_at")
            .values_list("code", flat=True)
        )
        referral_code = request.user.referral_owner_code or ""
        referral_link = f"{settings.FRONTEND_APP_URL.rstrip('/')}/register/?{urlencode({'ref': referral_code})}"

        serializer = ReferralSummarySerializer(
            data={
                "referral_code": referral_code,
                **referral_stats,
                "earned_rewards": earned_rewards,
                "referral_link": referral_link,
                "reward_coupon_codes": reward_coupon_codes,
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class CurrentUserView(APIView):
    """
    Return basic profile information for the authenticated user.

    Used by the frontend middleware to determine admin access without
    attempting a side-effecting request to a write endpoint.

    Response schema
    ---------------
    {
        "id": "<uuid>",
        "email": "user@example.com",
        "name": "Jane Doe",
        "is_staff": false,
        "role": "student"
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "is_staff": user.is_staff,
                "role": user.role,
            }
        )
