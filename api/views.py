from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from api.models import User, Hostel, Room, Asset, MaintenanceRequest
from api.serializers import (
    UserSerializer, UserRegisterSerializer, LoginSerializer,
    HostelSerializer, RoomSerializer, AssetSerializer, MaintenanceRequestSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class HostelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Hostels.
    Provides list, create, retrieve, update, delete operations.
    """
    queryset = Hostel.objects.all()
    serializer_class = HostelSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return super().get_permissions()


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Rooms.
    Provides list, create, retrieve, update, delete operations.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['room_number', 'hostel__name']
    ordering_fields = ['room_number', 'floor', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return super().get_permissions()


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Assets with search and quantity adjustment.
    GET /assets/ - List all assets (paginated, searchable)
    POST /assets/ - Create asset
    GET /assets/{id}/ - Retrieve asset
    PUT /assets/{id}/ - Update asset
    PATCH /assets/{id}/quantity/ - Adjust quantity
    DELETE /assets/{id}/ - Delete asset
    """
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'asset_type', 'room__room_number', 'room__hostel__name']
    ordering_fields = ['name', 'quantity', 'created_at', 'updated_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'])
    def quantity(self, request, pk=None):
        """
        PATCH /assets/{id}/quantity/
        Adjust asset quantity by a delta (+/-).
        Request body: {"quantity": 5} or {"quantity": -2}
        """
        asset = self.get_object()
        delta = request.data.get('quantity', 0)

        try:
            delta = int(delta)
        except (ValueError, TypeError):
            return Response(
                {'error': 'quantity must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        asset.quantity += delta
        if asset.quantity < 0:
            asset.quantity = 0

        asset.save()
        serializer = self.get_serializer(asset)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD API for maintenance requests.
    """

    queryset = MaintenanceRequest.objects.all()
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [SearchFilter, OrderingFilter]

    search_fields = [
        "title",
        "description",
        "status",
        "priority",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "priority",
        "status",
    ]

    ordering = ["-created_at"]


    
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /auth/register
    Register a new user.
    """
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/login
    Authenticate user and return JWT tokens.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

