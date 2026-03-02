from rest_framework import serializers


class AnalyticsSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_paid_orders = serializers.IntegerField()
    total_refunded_orders = serializers.IntegerField()
    refund_rate_percent = serializers.FloatField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_orders = serializers.IntegerField()
    last_7_days_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
