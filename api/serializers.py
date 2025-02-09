from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Product, Order, OrderItem


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'user_type']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 
                 'last_name', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Profile is automatically created by signal, just update it
        for attr, value in profile_data.items():
            setattr(user.profile, attr, value)
        user.profile.save()
        
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock']

    def validate_price(self, value):
        """
        Check that the price is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value

    def validate_stock(self, value):
        """
        Check that the stock is non-negative
        """
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'items', 'total_price', 'status']
        read_only_fields = ['total_price', 'status', 'customer']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        total_price = 0

        # Get customer from context
        customer = self.context['request'].user

        # Validate stock and calculate total price
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for product: {product.name}"
                )

            total_price += product.price * quantity

        # Create order with customer
        order = Order.objects.create(
            customer=customer,
            total_price=total_price,
            **validated_data
        )

        # Create order items and update stock
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            product.stock -= quantity
            product.save()

        return order