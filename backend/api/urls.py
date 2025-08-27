from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RenterViewSet,
    HostViewSet,
    WalletViewSet,
    TransactionViewSet,
    GPUViewSet,
    SessionViewSet,
    DashboardStatsView,
    AvailableGPUsView,
    TunnelManagementView,
    RegisterRenterView,
    RegisterHostView,
    EmailTokenObtainPairView,
    AgentDownloadView,
)

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class ApiRoot(APIView):
    """Simple public API root to return helpful endpoints."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'message': 'Welcome to the Labhya API',
            'routes': {
                'gpus_available': '/api/gpus/available/',
                'agent_download': '/api/agent/download/',
                'auth_login': '/api/auth/login/',
                'register_renter': '/api/auth/register/renter/',
                'register_host': '/api/auth/register/host/',
            }
        })

router = DefaultRouter()
router.register(r'renters', RenterViewSet, basename='renter')
router.register(r'hosts', HostViewSet, basename='host')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'gpus', GPUViewSet, basename='gpu')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    # Custom endpoints (must come before router to avoid conflicts)
    path('gpus/available/', AvailableGPUsView.as_view(), name='available-gpus'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('tunnels/manage/', TunnelManagementView.as_view(), name='tunnel-management'),
    path('agent/download/', AgentDownloadView.as_view(), name='agent-download'),
    # JWT Authentication endpoints (email-based login)
    path('auth/login/', EmailTokenObtainPairView.as_view(), name='jwt-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('auth/register/renter/', RegisterRenterView.as_view(), name='register-renter'),
    path('auth/register/host/', RegisterHostView.as_view(), name='register-host'),
    # Public root for tooling and health checks (before router so it matches /api/)
    path('', ApiRoot.as_view(), name='api-root'),
    # Router endpoints (must come last)
    path('', include(router.urls)),
]
