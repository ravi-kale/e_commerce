from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   request.user.profile.user_type == 'admin') or request.user.is_superuser

class IsCustomer(permissions.BasePermission):
    """
    Allows access only to customer users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   request.user.profile.user_type == 'customer')

class IsOrderOwner(permissions.BasePermission):
    """
    Allows access only to the order owner.
    """
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user

class ReadOnly(permissions.BasePermission):
    """
    Allows read-only access to any user (authenticated or not).
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS