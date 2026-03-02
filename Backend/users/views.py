from decimal import Decimal
from urllib.parse import urlencode

from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Coupon

from .models import Referral
from .serializers import ReferralSummarySerializer, RegisterUserSerializer


class RegisterUserView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterUserSerializer


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
        referral_link = request.build_absolute_uri(f"/register/?{urlencode({'ref': referral_code})}")

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
