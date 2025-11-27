from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework import viewsets
from django.http import Http404
from .models import Fundraiser, Pledge
from .serializers import FundraiserSerializer, PledgeSerializer, FundraiserDetailSerializer
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

class FundraiserViewSet(viewsets.ModelViewSet):
    queryset = Fundraiser.objects.all()
    serializer_class = FundraiserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)        

class PledgeList(APIView):

    def get(self, request):
        pledges = Pledge.objects.all()
        serializer = PledgeSerializer(pledges, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PledgeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(supporter=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )    
    
class PledgeViewSet(viewsets.ModelViewSet):
    queryset = Pledge.objects.all()
    serializer_class = PledgeSerializer
    permission_classes = [IsSupporterOrReadOnly]

    def create(self, request, *args, **kwargs):
        fundraiser_id = request.data.get('fundraiser')
        if not fundraiser_id:
            return Response({'detail': 'fundraiser id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            fundraiser = Fundraiser.objects.get(pk=fundraiser_id)
        except Fundraiser.DoesNotExist:
            return Response({'detail': 'fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        if not IsSupporterOrReadOnly.is_user_supporter_of_fundraiser(request.user, fundraiser):
            return Response({'detail': 'You must be a supporter to create a pledge'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)