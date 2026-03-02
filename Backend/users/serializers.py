from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Referral

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20)

    class Meta:
        model = User
        fields = ("id", "name", "email", "password", "role", "referral_owner_code", "referral_code")
        read_only_fields = ("id", "role", "referral_owner_code")

    def validate_referral_code(self, value):
        return value.strip().upper()

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", "")
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            if referral_code:
                referrer = User.objects.filter(referral_owner_code=referral_code).first()
                if not referrer:
                    raise serializers.ValidationError({"referral_code": "Invalid referral code."})
                if referrer.id == user.id:
                    raise serializers.ValidationError({"referral_code": "You cannot use your own referral code."})
                Referral.objects.create(referrer=referrer, referred_user=user)
        return user
