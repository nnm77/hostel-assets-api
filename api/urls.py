from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    HostelViewSet, RoomViewSet, AssetViewSet,MaintenanceRequestViewSet,
    register, login
)

router = DefaultRouter()
router.register(r'hostels', HostelViewSet, basename='hostel')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r"maintenance-requests",MaintenanceRequestViewSet,basename="maintenance-request")

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register', register, name='register'),
    path('auth/login', login, name='login'),
]
