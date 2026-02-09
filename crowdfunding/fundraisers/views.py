from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated

from .models import Fundraiser, Pledge
from .serializers import (FundraiserSerializer, FundraiserDetailSerializer, PledgeSerializer, InvitationSerializer)
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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    def post(self, request):
        serializer = InvitationSerializer(data=request.data)
        if serializer.is_valid():
            fundraiser = get_object_or_404(Fundraiser, pk=serializer.validated_data["fundraiser"])
            user = get_object_or_404(get_user_model(), pk=serializer.validated_data["user"])
            self.check_object_permissions(self.request, fundraiser)
            fundraiser.supporters.add(user)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)