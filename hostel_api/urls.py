"""
URL configuration for hostel_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class HealthCheck(APIView):
    """Simple health check for the API root.

    This endpoint is explicitly marked AllowAny so it's publicly accessible
    (monitoring, health checks, and docs discovery) while the rest of the
    API remains protected by the project's default JWT-based permissions.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "docs": "/docs"})


urlpatterns = [
    path('', HealthCheck.as_view(), name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
