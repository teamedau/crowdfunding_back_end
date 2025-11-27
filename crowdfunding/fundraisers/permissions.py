from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsSupporterOrReadOnly(permissions.BasePermission):
    """
    Allow create a pledge only if the user is a fundraiser.supporter.
    Anyone can see, to create we check membership.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # To create post we need it to be authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only the creator can modify the pledge
        from .models import Pledge, Fundraiser
        if isinstance(obj, Pledge):
            return obj.supporter == request.user
        if isinstance(obj, Fundraiser):
            # only owner can modify fundraisers
            return obj.owner == request.user
        return False

    #This is to verify membership before creating a pledge in the viewset?
    @staticmethod
    def is_user_supporter_of_fundraiser(user, fundraiser):
        return fundraiser.supporters.filter(pk=user.pk).exists()