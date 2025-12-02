"""
API views for user profile management
"""
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CustomUser
from .serializers import CustomUserSerializer


@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    API endpoint to get and update user profile details.
    Returns all personal details stored in the database.
    
    This endpoint uses token-based authentication (Token or JWT) to avoid CSRF requirements.
    It's designed for API clients (mobile apps) that use token authentication.
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = CustomUserSerializer(user, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

