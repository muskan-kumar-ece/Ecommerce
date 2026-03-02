from rest_framework import serializers


class AnalyticsSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    gross_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_paid_orders = serializers.IntegerField()
    total_refunded_orders = serializers.IntegerField()
    total_referrals = serializers.IntegerField()
    successful_referrals = serializers.IntegerField()
    revenue_from_referrals = serializers.DecimalField(max_digits=12, decimal_places=2)
    refund_rate_percent = serializers.FloatField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_orders = serializers.IntegerField()
    last_7_days_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
