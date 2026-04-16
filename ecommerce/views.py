from .serializers import (RegisterUserSerializer, CustomTokenObtainPairSerializer, UserProfileSerializer,
                          ChangePasswordSerializer, ProductSerializer, CategorySerializer, CartSerializer,
                            CartItemSerializer, OrderSerializer, OrderItemSerializer)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from rest_framework.decorators import action
from django.db import transaction
from drf_spectacular.utils import extend_schema

class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'status': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'email': user.email,
            'username': user.username,
            'phone_number': user.phone_number,
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        })
    
    def patch(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User profile update successfully.',
                'status': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={200: None, 400: None})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully.', 'status': True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_or_create_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart = self.get_or_create_cart()
        serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart retrieved successfully.',
            'status': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_or_create_cart()
        product_id = request.data.get('product')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({
                'message': 'Product is required.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({
                'message': 'Quantity must be a positive integer.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'message': 'Product not found.',
                'status': False
            }, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response({
            'message': 'Item added to cart successfully.',
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_item(self, request, pk=None):
        cart = self.get_or_create_cart()
        quantity = request.data.get('quantity')

        if not quantity:
            return Response({
                'message': 'Quantity is required.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({
                'message': 'Quantity must be a positive integer.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = CartItem.objects.get(id=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({
                'message': 'Cart item not found.',
                'status': False
            }, status=status.HTTP_404_NOT_FOUND)

        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        return Response({
            'message': 'Item updated successfully.',
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        cart = self.get_or_create_cart()

        try:
            cart_item = CartItem.objects.get(id=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({
                'message': 'Cart item not found.',
                'status': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = self.get_queryset()
        serializer = OrderSerializer(orders, many=True)
        return Response({
            'message': 'Orders gotten successfully.',
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def order(self, request, pk=None):
        try:
            order_item = Order.objects.get(user=self.request.user, id=pk)
        except Order.DoesNotExist:
            return Response({
                'message': 'Order not found.',
                'status': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order_item)
        return Response({
            'message': 'Order gotten successfully.',
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def place_order(self, request):
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.select_related('product').all()    

        # check if cart is empty
        if not cart_items.exists():
            return Response({
                'message': 'Your cart is empty. Unable to place order.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)    

        # validate stock for all items
        for item in cart_items:
            if item.quantity > item.product.stock:
                return Response({
                    'message': f'Not enough stock for {item.product.name}. Available: {item.product.stock}.',
                    'status': False
                }, status=status.HTTP_400_BAD_REQUEST)    

        with transaction.atomic():
            # calculate total
            total_price = sum(item.product.price * item.quantity for item in cart_items)    

            # create order
            order = Order.objects.create(user=user, total_price=total_price)    

            # create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # deduct stock
                item.product.stock -= item.quantity
                item.product.save()    

            # clear cart
            cart_items.delete()    

        serializer = OrderSerializer(order)
        return Response({
            'message': 'Order placed successfully.',
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def cancel_order(self, request, pk=None):
        try:
            order = Order.objects.get(user=request.user, id=pk)
        except Order.DoesNotExist:
            return Response({
                'message': 'Order not found.',
                'status': False
            }, status=status.HTTP_404_NOT_FOUND)
    
        if order.status == 'cancelled':
            return Response({
                'message': 'Order is already cancelled.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
        if order.status != 'pending':
            return Response({
                'message': 'Only pending orders can be cancelled.',
                'status': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
        with transaction.atomic():
            # restore stock
            for item in order.items.select_related('product').all():
                item.product.stock += item.quantity
                item.product.save()
    
            order.status = 'cancelled'
            order.save()
    
        return Response({
            'message': 'Your order has been cancelled.',
            'status': False
        }, status=status.HTTP_200_OK)
