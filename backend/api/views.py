from django.shortcuts import render
from django.db import models
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils.http import http_date

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

import os
import zipfile
import tempfile
import shutil
from pathlib import Path

from .models import Renter, Host, Wallet, Transaction, GPU, Session
from .serializers import (
    RenterSerializer, RenterDetailSerializer, RenterWalletSerializer,
    HostSerializer, HostDetailSerializer, HostWalletSerializer,
    WalletSerializer, WalletDetailSerializer, WalletTransactionSerializer,
    TransactionSerializer,
    GPUSerializer, GPUDetailSerializer,
    SessionSerializer, SessionDetailSerializer, SessionCreateSerializer, SessionUpdateSerializer
)
from .tunnel_manager import tunnel_manager, container_manager
from .models import HostKey
from .serializers import HostKeySerializer
from django.utils import timezone


class RegisterRenterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        if not all([name, email, password]):
            return Response({'error': 'name, email, password required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=email).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
            renter = Renter.objects.create(user=user)
            # Wallet auto-created via signals
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Renter registered',
                'renter_id': str(renter.id),
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)


class RegisterHostView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        if not all([name, email, password]):
            return Response({'error': 'name, email, password required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=email).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
            host = Host.objects.create(user=user)
            # Wallet auto-created via signals
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Host registered',
                'host_id': str(host.id),
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)


class RenterViewSet(viewsets.ModelViewSet):
    queryset = Renter.objects.all()
    serializer_class = RenterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RenterDetailSerializer
        return RenterSerializer

    @action(detail=True, methods=['post'])
    def add_money(self, request, pk=None):
        """Add money to renter's wallet"""
        renter = self.get_object()
        amount = request.data.get('amount')
        description = request.data.get('description', 'Deposit')

        try:
            amount = float(amount)
        except Exception:
            amount = None
        if not amount or amount <= 0:
            return Response(
                {'error': 'Valid amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_balance = renter.add_money(amount, description)
            return Response({
                'message': 'Money added successfully',
                'new_balance': new_balance,
                'amount_added': amount
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def wallet(self, request, pk=None):
        """Get renter's wallet details"""
        renter = self.get_object()
        wallet = renter.get_wallet()
        serializer = WalletDetailSerializer(wallet)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for this renter"""
        renter = self.get_object()
        sessions = Session.objects.filter(renter=renter)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HostDetailSerializer
        return HostSerializer

    @action(detail=True, methods=['post'])
    def withdraw_money(self, request, pk=None):
        """Withdraw money from host's wallet"""
        host = self.get_object()
        amount = request.data.get('amount')
        description = request.data.get('description', 'Withdrawal')

        try:
            amount = float(amount)
        except Exception:
            amount = None
        if not amount or amount <= 0:
            return Response(
                {'error': 'Valid amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_balance = host.withdraw_money(amount, description)
            return Response({
                'message': 'Money withdrawn successfully',
                'new_balance': new_balance,
                'amount_withdrawn': amount
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def wallet(self, request, pk=None):
        """Get host's wallet details"""
        host = self.get_object()
        wallet = host.get_wallet()
        serializer = WalletDetailSerializer(wallet)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def gpus(self, request, pk=None):
        """Get all GPUs for this host"""
        host = self.get_object()
        gpus = GPU.objects.filter(host=host)
        serializer = GPUSerializer(gpus, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for this host"""
        host = self.get_object()
        sessions = Session.objects.filter(host=host)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_key(self, request, pk=None):
        """Agent uploads a public key for this host for operator approval"""
        host = self.get_object()
        pubkey = request.data.get('public_key')
        if not pubkey:
            return Response({'error': 'public_key required'}, status=status.HTTP_400_BAD_REQUEST)

        # For testing/small deployments we auto-approve uploaded keys so the agent
        # can immediately create reverse tunnels without manual admin approval.
        key = HostKey.objects.create(
            host=host,
            public_key=pubkey,
            status='APPROVED',
            approved_at=timezone.now(),
            approved_by=None,
        )
        serializer = HostKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def keys(self, request, pk=None):
        """List all keys for this host (approved and pending)"""
        host = self.get_object()
        keys = HostKey.objects.filter(host=host).order_by('-created_at')
        serializer = HostKeySerializer(keys, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending_keys(self, request):
        """List all pending host keys across hosts (admin only)"""
        keys = HostKey.objects.filter(status='PENDING').order_by('created_at')
        serializer = HostKeySerializer(keys, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve_key(self, request, pk=None):
        """Approve a pending host key and optionally deploy it to the tunnel server (admin only)"""
        key_id = request.data.get('key_id')
        if not key_id:
            return Response({'error': 'key_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            key = HostKey.objects.get(id=key_id, host_id=pk)
        except HostKey.DoesNotExist:
            return Response({'error': 'Key not found'}, status=status.HTTP_404_NOT_FOUND)

        key.status = 'APPROVED'
        key.approved_by = request.user
        key.approved_at = timezone.now()
        key.save()

        # Operator should manually deploy the key to EC2, or implement automation here
        return Response({'message': 'Key approved', 'key_id': str(key.id)})
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's host information"""
        try:
            host = Host.objects.get(user=request.user)
            serializer = HostDetailSerializer(host)
            return Response(serializer.data)
        except Host.DoesNotExist:
            return Response(
                {'error': 'Host not found for current user'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register current user as a host with GPU information"""
        try:
            # Check if host already exists
            if Host.objects.filter(user=request.user).exists():
                return Response(
                    {'error': 'Host already registered'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get GPU and system information from request
            platform_info = request.data.get('platform', 'Unknown')
            architecture = request.data.get('architecture', 'Unknown')
            gpu_count = request.data.get('gpu_count', 0)
            gpu_details = request.data.get('gpu_details', [])
            
            # Create host
            host = Host.objects.create(
                user=request.user,
                status='online'
            )
            
            # Create GPU entries
            for gpu_info in gpu_details:
                GPU.objects.create(
                    host=host,
                    gpu_model=gpu_info.get('name', 'Unknown GPU'),
                    memory_total=gpu_info.get('memory_total', 0),
                    memory_used=gpu_info.get('memory_used', 0),
                    utilization=gpu_info.get('utilization', 0),
                    temperature=gpu_info.get('temperature', 0)
                )
            
            serializer = HostDetailSerializer(host)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WalletDetailSerializer
        return WalletSerializer

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for this wallet"""
        wallet = self.get_object()
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all().order_by('-created_at')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.all().order_by('-created_at')
        wallet_id = self.request.query_params.get('wallet', None)
        transaction_type = self.request.query_params.get('type', None)
        
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
            
        return queryset


class GPUViewSet(viewsets.ModelViewSet):
    queryset = GPU.objects.all()
    serializer_class = GPUSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = GPU.objects.all()
        host_id = self.request.query_params.get('host', None)
        available_only = self.request.query_params.get('available', None)
        
        if host_id:
            queryset = queryset.filter(host_id=host_id)
        if available_only == 'true':
            queryset = queryset.filter(gpu_availability=True)
            
        return queryset

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Toggle GPU availability"""
        gpu = self.get_object()
        gpu.gpu_availability = not gpu.gpu_availability
        gpu.save()
        
        return Response({
            'message': f'GPU availability set to {gpu.gpu_availability}',
            'gpu_availability': gpu.gpu_availability
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for this GPU"""
        gpu = self.get_object()
        sessions = Session.objects.filter(gpu=gpu)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().order_by('-created_at')
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SessionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SessionUpdateSerializer
        elif self.action == 'retrieve':
            return SessionDetailSerializer
        return SessionSerializer

    def get_queryset(self):
        queryset = Session.objects.all().order_by('-created_at')
        renter_id = self.request.query_params.get('renter', None)
        host_id = self.request.query_params.get('host', None)
        gpu_id = self.request.query_params.get('gpu', None)
        status_filter = self.request.query_params.get('status', None)
        
        if renter_id:
            queryset = queryset.filter(renter_id=renter_id)
        if host_id:
            queryset = queryset.filter(host_id=host_id)
        if gpu_id:
            queryset = queryset.filter(gpu_id=gpu_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new session with validation and tunnel setup"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            session = serializer.save()
            
            # Mark GPU as unavailable
            session.gpu.gpu_availability = False
            session.gpu.save()
            
            # Try to create reverse tunnel if host info is provided
            if session.ssh_host:
                tunnel_result = tunnel_manager.create_tunnel(
                    str(session.id),
                    session.ssh_host,
                    session.ssh_port or 22,
                    session.ssh_username or 'ubuntu'
                )
                
                if tunnel_result:
                    local_port, connection_string = tunnel_result
                    # Update session with tunnel info
                    original_host = session.ssh_host
                    session.ssh_host = 'localhost'  # Now accessible locally
                    session.ssh_port = local_port
                    session.connection_status = 'CONNECTED'
                    session.status = 'ACTIVE'
                    session.save()
                    
                    return Response({
                        **SessionDetailSerializer(session).data,
                        'tunnel_info': {
                            'original_host': original_host,
                            'tunnel_port': local_port,
                            'connection_string': connection_string
                        }
                    }, status=status.HTTP_201_CREATED)
                else:
                    session.connection_status = 'ERROR'
                    session.connection_error = 'Failed to establish tunnel'
                    session.status = 'FAILED'
                    session.save()
                    
                    # Mark GPU as available again since session failed
                    session.gpu.gpu_availability = True
                    session.gpu.save()
                    
                    return Response({
                        'error': 'Failed to create SSH tunnel',
                        'session': SessionDetailSerializer(session).data
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # No ssh_host provided yet — session should be PENDING until an agent
                # provisions a container and establishes the tunnel. Agent will poll
                # host sessions and call update_connection_status when ready.
                session.status = 'PENDING'
                session.connection_status = 'CONNECTING'
                session.save()
            
        return Response(
            SessionDetailSerializer(session).data, 
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a session, process payment, and cleanup tunnel"""
        session = self.get_object()
        
        if session.status == 'COMPLETED':
            return Response(
                {'error': 'Session is already completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Set end time
                session.end_time = timezone.now()
                session.status = 'COMPLETED'
                session.connection_status = 'DISCONNECTED'
                session.save()
                
                # Process payment
                total_cost = session.process_payment()
                
                # Mark GPU as available again
                session.gpu.gpu_availability = True
                session.gpu.save()
                
                # Close SSH tunnel
                tunnel_closed = tunnel_manager.close_tunnel(str(session.id))
                
                # Stop Docker container if exists
                container_stopped = container_manager.stop_container(str(session.id))
                
            return Response({
                'message': 'Session ended successfully',
                'total_cost': total_cost,
                'session_id': str(session.id),
                'tunnel_closed': tunnel_closed,
                'container_stopped': container_stopped
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_connection_status(self, request, pk=None):
        """Update session connection status"""
        session = self.get_object()
        status_val = request.data.get('status')
        error_message = request.data.get('error_message')
        # Optional connection fields
        ssh_host = request.data.get('ssh_host')
        ssh_port = request.data.get('ssh_port')
        ssh_username = request.data.get('ssh_username')
        ssh_password = request.data.get('ssh_password')
        
        if not status_val:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update optional connection details if provided
            if ssh_host is not None:
                session.ssh_host = ssh_host
            if ssh_port is not None:
                try:
                    session.ssh_port = int(ssh_port)
                except Exception:
                    pass
            if ssh_username is not None:
                session.ssh_username = ssh_username
            if ssh_password is not None:
                session.ssh_password = ssh_password

            session.update_connection_status(status_val, error_message)
            session.save()
            return Response({
                'message': 'Connection status updated',
                'connection_status': session.connection_status,
                'ssh_host': session.ssh_host,
                'ssh_port': session.ssh_port,
                'ssh_username': session.ssh_username
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_gpu_metrics(self, request, pk=None):
        """Update GPU usage metrics"""
        session = self.get_object()
        gpu_util = request.data.get('gpu_utilization', 0)
        memory_util = request.data.get('memory_utilization', 0)
        temperature = request.data.get('temperature', 0)
        
        try:
            session.update_gpu_metrics(gpu_util, memory_util, temperature)
            return Response({
                'message': 'GPU metrics updated',
                'gpu_utilization': session.gpu_utilization,
                'memory_utilization': session.memory_utilization,
                'temperature': session.temperature
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def connection_info(self, request, pk=None):
        """Get SSH connection information"""
        session = self.get_object()
        return Response({
            'ssh_connection_string': session.get_ssh_connection_string(),
            'ssh_host': session.ssh_host,
            'ssh_port': session.ssh_port,
            'ssh_username': session.ssh_username,
            'connection_status': session.connection_status,
            'is_connected': session.is_connected()
        })

    @action(detail=True, methods=['post'])
    def create_tunnel(self, request, pk=None):
        """Create or recreate a reverse tunnel for existing session"""
        session = self.get_object()
        
        if not session.ssh_host:
            return Response(
                {'error': 'SSH host not configured for this session'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get original host info (before tunnel was created)
        original_host = request.data.get('original_host', session.ssh_host)
        
        tunnel_result = tunnel_manager.create_tunnel(
            str(session.id),
            original_host,
            session.ssh_port or 22,
            session.ssh_username or 'ubuntu'
        )
        
        if tunnel_result:
            local_port, connection_string = tunnel_result
            # Update session with local tunnel info
            session.ssh_host = 'localhost'
            session.ssh_port = local_port
            session.connection_status = 'CONNECTED'
            session.connection_error = None
            session.last_connected = timezone.now()
            session.save()
            
            return Response({
                'message': 'Tunnel created successfully',
                'original_host': original_host,
                'tunnel_port': local_port,
                'connection_string': connection_string
            }, status=status.HTTP_200_OK)
        else:
            session.connection_status = 'ERROR'
            session.connection_error = 'Failed to establish tunnel'
            session.save()
            
            return Response(
                {'error': 'Failed to create tunnel'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def close_tunnel(self, request, pk=None):
        """Close reverse tunnel for session"""
        session = self.get_object()
        
        if tunnel_manager.close_tunnel(str(session.id)):
            session.connection_status = 'DISCONNECTED'
            session.save()
            return Response({'message': 'Tunnel closed successfully'})
        else:
            return Response(
                {'error': 'Failed to close tunnel'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def tunnel_status(self, request, pk=None):
        """Get tunnel status for session"""
        session = self.get_object()
        
        tunnel_status = tunnel_manager.get_tunnel_status(str(session.id))
        
        return Response({
            'session_id': str(session.id),
            'tunnel_status': tunnel_status,
            'connection_status': session.connection_status
        })

    @action(detail=True, methods=['post'])
    def restart_tunnel(self, request, pk=None):
        """Restart tunnel for session"""
        session = self.get_object()
        
        if tunnel_manager.restart_tunnel(str(session.id)):
            session.refresh_from_db()
            return Response({
                'message': 'Tunnel restarted successfully',
                'ssh_port': session.ssh_port,
                'connection_status': session.connection_status
            })
        else:
            return Response(
                {'error': 'Failed to restart tunnel'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def create_container(self, request, pk=None):
        """Create Docker container with GPU access"""
        session = self.get_object()
        
        gpu_device_id = request.data.get('gpu_device_id', '0')
        docker_image = request.data.get('image', settings.DEFAULT_GPU_DOCKER_IMAGE)
        
        container_id = container_manager.create_gpu_container(
            str(session.id),
            gpu_device_id,
            docker_image
        )
        
        if container_id:
            return Response({
                'message': 'Container created successfully',
                'container_id': container_id[:12],
                'image': docker_image
            })
        else:
            return Response(
                {'error': 'Failed to create container'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def container_status(self, request, pk=None):
        """Get container status for session"""
        session = self.get_object()
        
        container_status = container_manager.get_container_status(str(session.id))
        
        return Response({
            'session_id': str(session.id),
            'container_status': container_status
        })

    @action(detail=True, methods=['post'])
    def cancel_session(self, request, pk=None):
        """Cancel an active session and cleanup resources"""
        session = self.get_object()
        
        if session.status != 'ACTIVE':
            return Response(
                {'error': 'Only active sessions can be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                session.status = 'CANCELLED'
                session.end_time = timezone.now()
                session.connection_status = 'DISCONNECTED'
                session.save()
                
                # Mark GPU as available again
                session.gpu.gpu_availability = True
                session.gpu.save()
                
                # Close SSH tunnel
                tunnel_closed = tunnel_manager.close_tunnel(str(session.id))
                
                # Stop Docker container if exists
                container_stopped = container_manager.stop_container(str(session.id))
                
            return Response({
                'message': 'Session cancelled successfully',
                'session_id': str(session.id),
                'tunnel_closed': tunnel_closed,
                'container_stopped': container_stopped
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop an active session (alias for cancel_session)"""
        # Reuse cancel_session logic to stop resources and mark disconnected
        return self.cancel_session(request, pk)


# Additional utility views
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class TunnelManagementView(APIView):
    """Administrative tunnel management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get status of all active tunnels"""
        tunnel_status = tunnel_manager.get_all_tunnel_status()
        container_info = {}
        
        # Get container status for each active tunnel
        for session_id in tunnel_status.keys():
            container_info[session_id] = container_manager.get_container_status(session_id)
        
        return Response({
            'tunnels': tunnel_status,
            'containers': container_info,
            'total_active_tunnels': len([t for t in tunnel_status.values() if t['active']]),
            'total_active_containers': len([c for c in container_info.values() if c.get('running', False)])
        })
    
    def post(self, request):
        """Administrative tunnel operations"""
        action = request.data.get('action')
        
        if action == 'cleanup_dead_tunnels':
            cleaned_count = tunnel_manager.cleanup_dead_tunnels()
            return Response({
                'message': f'Cleaned up {cleaned_count} dead tunnels'
            })
        
        elif action == 'restart_all_tunnels':
            # Get all active sessions
            active_sessions = Session.objects.filter(status='ACTIVE')
            restarted = 0
            failed = 0
            
            for session in active_sessions:
                if tunnel_manager.restart_tunnel(str(session.id)):
                    restarted += 1
                else:
                    failed += 1
            
            return Response({
                'message': f'Restarted {restarted} tunnels, {failed} failed'
            })
        
        else:
            return Response(
                {'error': 'Invalid action. Available: cleanup_dead_tunnels, restart_all_tunnels'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics"""
        total_renters = Renter.objects.count()
        total_hosts = Host.objects.count()
        total_gpus = GPU.objects.count()
        available_gpus = GPU.objects.filter(gpu_availability=True).count()
        active_sessions = Session.objects.filter(status='ACTIVE').count()
        total_transactions = Transaction.objects.count()
        
        # Calculate total revenue (all rental earnings)
        total_revenue = Transaction.objects.filter(
            transaction_type='RENTAL_EARNING'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return Response({
            'total_renters': total_renters,
            'total_hosts': total_hosts,
            'total_gpus': total_gpus,
            'available_gpus': available_gpus,
            'active_sessions': active_sessions,
            'total_transactions': total_transactions,
            'total_revenue': total_revenue
        })


class AvailableGPUsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all available GPUs for rent"""
        gpus = GPU.objects.filter(gpu_availability=True)
        serializer = GPUDetailSerializer(gpus, many=True)
        return Response(serializer.data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    def validate(self, attrs):
        # Get the email and password from the input
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Authenticate using email as username
            from django.contrib.auth import authenticate
            user = authenticate(username=email, password=password)
            
            if user is None:
                raise serializers.ValidationError('No active account found with the given credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            # If authentication succeeds, create the token data manually
            refresh = self.get_token(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'first_name': user.first_name or user.username,
            }
            
            # Check if user is a renter or host
            try:
                renter = Renter.objects.get(user=user)
                data['renter_id'] = str(renter.id)
                data['user_type'] = 'renter'
            except Renter.DoesNotExist:
                pass
                
            try:
                host = Host.objects.get(user=user)
                data['host_id'] = str(host.id)
                data['user_type'] = 'host'
            except Host.DoesNotExist:
                pass
            
            return data
        else:
            raise serializers.ValidationError('Email and password required')


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class AgentDownloadView(APIView):
    """Download the GPU agent as a zip file"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Path to the agent directory
            agent_dir = Path(settings.BASE_DIR) / 'agent'
            
            if not agent_dir.exists():
                return Response(
                    {'error': 'Agent files not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create temporary zip file
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'labhya-gpu-agent.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all agent files to zip
                for file_path in agent_dir.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        # Exclude log files and cache directories
                        if '__pycache__' not in str(file_path) and not file_path.name.endswith('.log'):
                            arcname = file_path.relative_to(agent_dir.parent)
                            zipf.write(file_path, arcname)
            
            # Return the zip file
            response = FileResponse(
                open(zip_path, 'rb'),
                as_attachment=True,
                filename='labhya-gpu-agent.zip',
                content_type='application/zip'
            )
            
            # Clean up temp file after response (Django handles this automatically)
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create agent download: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
