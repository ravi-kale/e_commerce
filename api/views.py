from rest_framework import viewsets, status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Product, Order, User
from .serializers import ProductSerializer, OrderSerializer, UserSerializer
from .permissions import IsAdminUser, IsCustomer, IsOrderOwner, ReadOnly

class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Allows anonymous users to register.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for products.
    - Anonymous users can view products
    - Admin users can create/update/delete products
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [ReadOnly|IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Create a new product with validation
        """
        if not request.user.profile.is_admin():
            return Response(
                {'error': 'Only admin users can create products'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders.
    - Authenticated customers can create and view their orders
    - Admin users can view all orders
    - Anonymous users have no access
    """
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'head', 'options']  # Limit available methods

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsCustomer]
        elif self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & (IsOrderOwner|IsAdminUser)]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.profile.is_admin():
            return Order.objects.all()
        return Order.objects.filter(customer=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new order with stock validation
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def list(self, request, *args, **kwargs):
        """
        List orders with proper error handling for anonymous users
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to view orders'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve single order with proper error handling
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to view order'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            return super().retrieve(request, *args, **kwargs)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )