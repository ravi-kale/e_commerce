from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from .models import UserProfile, Product, Order, OrderItem

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        
        # Create test user data
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'profile': {
                'phone': '1234567890',
                'address': 'Test Address'
            }
        }

    def test_user_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(UserProfile.objects.filter(user__username='testuser').exists())

    def test_user_registration_duplicate_username(self):
        # Create first user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to create user with same username
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        # Create user first
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to login
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_wrong_credentials(self):
        response = self.client.post(self.token_url, {
            'username': 'wronguser',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ProductTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.products_url = reverse('product-list')
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_product',
            password='admin123',
            is_staff=True,
            is_active=True
        )
        # Set admin profile
        self.admin_profile = UserProfile.objects.get(user=self.admin_user)
        self.admin_profile.user_type = 'admin'
        self.admin_profile.save()
        self.admin_user.refresh_from_db()
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer_product',
            password='customer123',
            is_active=True
        )
        # Set customer profile
        self.customer_profile = UserProfile.objects.get(user=self.customer_user)
        self.customer_profile.user_type = 'customer'
        self.customer_profile.save()
        self.customer_profile.refresh_from_db()
        
        # Create test product data
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'stock': 100
        }

    def test_create_product_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.products_url, self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.get().name, 'Test Product')

    def test_create_product_as_customer_forbidden(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.products_url, self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_invalid_data(self):
        self.client.force_authenticate(user=self.admin_user)
        invalid_product_data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '-10.00',  # Invalid negative price
            'stock': 100
        }
        response = self.client.post(self.products_url, invalid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_list_products_no_auth_required(self):
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class OrderTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.orders_url = reverse('order-list')
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            password='customer123'
        )
        
        # Create product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=100
        )
        
        # Create order data
        self.order_data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2
                }
            ]
        }

    def test_view_order_unauthorized(self):
        # Create an order
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.orders_url, self.order_data, format='json')
        order_id = response.data['id']
        
        # Try to access without authentication
        self.client.force_authenticate(user=None)
        # Fix the URL formatting
        detail_url = reverse('order-detail', kwargs={'pk': order_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_success(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.orders_url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        
        # Check if stock was updated
        updated_product = Product.objects.get(id=self.product.id)
        self.assertEqual(updated_product.stock, 98)

    def test_create_order_insufficient_stock(self):
        self.client.force_authenticate(user=self.customer_user)
        order_data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 101  # More than available stock
                }
            ]
        }
        response = self.client.post(self.orders_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_orders_as_customer(self):
        self.client.force_authenticate(user=self.customer_user)
        # Create an order first
        self.client.post(self.orders_url, self.order_data, format='json')
        
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_profile_created_automatically(self):
        """Test that a UserProfile is automatically created when a User is created"""
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_profile_str_method(self):
        """Test the string representation of UserProfile"""
        profile = self.user.profile
        self.assertEqual(str(profile), self.user.username)

    def test_is_admin_method(self):
        """Test the is_admin method of UserProfile"""
        profile = self.user.profile
        profile.user_type = 'admin'
        profile.save()
        self.assertTrue(profile.is_admin())
        
        profile.user_type = 'customer'
        profile.save()
        self.assertFalse(profile.is_admin())

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=100
        )

    def test_product_str_method(self):
        """Test the string representation of Product"""
        self.assertEqual(str(self.product), 'Test Product')

    def test_order_creation(self):
        """Test Order creation and related OrderItem"""
        order = Order.objects.create(
            customer=self.user,
            total_price=Decimal('199.98')
        )
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order_item.price, Decimal('99.99'))