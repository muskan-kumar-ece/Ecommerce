from rest_framework import serializers


class ChatbotMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True)
