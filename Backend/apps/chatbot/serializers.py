from rest_framework import serializers


class ChatbotMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True)

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("Message is required.")
        return value
