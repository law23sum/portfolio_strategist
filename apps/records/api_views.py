from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ReceiptSerializer

from rest_framework.permissions import IsAuthenticated


class ReceiptUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ReceiptSerializer(data = request.data)
        if serializer.is_valid():
            # The owner always comes from the authenticated request, never from client input.
            serializer.save(user = request.user)
            return Response(serializer.data, status = 201)
        return Response(serializer.errors, status = 400)