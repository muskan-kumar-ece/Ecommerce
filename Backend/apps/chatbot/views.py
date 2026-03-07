from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ChatbotMessageSerializer
from .services import build_chatbot_response


class ChatbotMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatbotMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_payload = build_chatbot_response(request.user, serializer.validated_data["message"])
        return Response(response_payload, status=status.HTTP_200_OK)
