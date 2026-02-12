from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated

from .models import Fundraiser, Pledge, Invitation
from .serializers import (FundraiserSerializer, FundraiserDetailSerializer, PledgeSerializer, InvitationSerializer, UserSearchSerializer, CreateInvitationSerializer)
from .permissions import IsOwnerOrReadOnly, IsSupporterOrReadOnly

class FundraiserList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
            fundraisers = Fundraiser.objects.all()
            serializer = FundraiserSerializer(fundraisers, many=True)
            return Response(serializer.data)
        
    def post(self, request):
            serializer = FundraiserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
class FundraiserDetail(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly
    ]
    
    def get_object(self, pk):
        try:
            fundraiser = Fundraiser.objects.get(pk=pk)
            self.check_object_permissions(self.request, fundraiser)
            return fundraiser
        except Fundraiser.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        fundraiser = self.get_object(pk)
        serializer = FundraiserDetailSerializer(fundraiser)
        return Response(serializer.data)
    
    def put(self, request, pk):
        fundraiser = self.get_object(pk)
        serializer = FundraiserDetailSerializer(
            instance=fundraiser,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, pk):
        fundraiser = self.get_object(pk)
        fundraiser.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PledgeList(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        pledges = Pledge.objects.all()
        serializer = PledgeSerializer(pledges, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PledgeSerializer(
            data=request.data,
            context={"request": request}
            )
        if serializer.is_valid():
            if not IsSupporterOrReadOnly.is_user_supporter_of_fundraiser(request.user, serializer.validated_data["fundraiser"]):
            
                return Response({'detail': 'You must be a supporter to create a pledge'}, status=status.HTTP_403_FORBIDDEN)
            serializer.save(supporter=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )    
    
class InvitationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateInvitationSerializer(data=request.data)
        if serializer.is_valid():
            fundraiser = get_object_or_404(Fundraiser, pk=serializer.validated_data["fundraiser_id"])
            
            # Solo el owner puede invitar
            if fundraiser.owner != request.user:
                return Response(
                    {'detail': 'Only the fundraiser owner can send invitations'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            invited_user = get_object_or_404(get_user_model(), pk=serializer.validated_data["user_id"])
            
            # Verificar si ya existe una invitación
            existing = Invitation.objects.filter(
                fundraiser=fundraiser,
                invited_user=invited_user
            ).first()
            
            if existing:
                if existing.status == 'pending':
                    return Response({'detail': 'Invitation already sent'}, status=status.HTTP_400_BAD_REQUEST)
                elif existing.status == 'accepted':
                    return Response({'detail': 'User already accepted'}, status=status.HTTP_400_BAD_REQUEST)
            
            invitation = Invitation.objects.create(
                fundraiser=fundraiser,
                invited_user=invited_user,
                invited_by=request.user,
                status='pending'
            )
            
            response_serializer = InvitationSerializer(invitation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class FundraiserUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        fundraisers = Fundraiser.objects.filter(owner=request.user)
        serializer = FundraiserSerializer(fundraisers, many=True)
        return Response(serializer.data)
    
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({'results': []})
        
        users = get_user_model().objects.filter(
            models.Q(username__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(email__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        serializer = UserSearchSerializer(users, many=True)
        return Response({'results': serializer.data})

class MyInvitationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        invitations = Invitation.objects.filter(
            invited_user=request.user,
            status='pending'
        ).select_related('fundraiser', 'invited_by')
        
        serializer = InvitationSerializer(invitations, many=True)
        return Response(serializer.data)

class InvitationActionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk, invited_user=request.user)
        
        action = request.data.get('action')
        if action not in ['accept', 'reject']:
            return Response({'detail': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
        if invitation.status != 'pending':
            return Response({'detail': 'Invitation already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        if action == 'accept':
            invitation.status = 'accepted'
            invitation.save()
            # Agregar usuario como supporter
            invitation.fundraiser.supporters.add(request.user)
            return Response({'detail': 'Invitation accepted'})
        else:
            invitation.status = 'rejected'
            invitation.save()
            return Response({'detail': 'Invitation rejected'})