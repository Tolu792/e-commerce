from rest_framework import serializers
from .models import User, Product, Category, Cart, CartItem
import re
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken

def validate_image(value):
    allowed_formats = ['image/jpeg', 'image/png', 'image/webp']
    if value.content_type not in allowed_formats:
        raise serializers.ValidationError("Only JPEG, PNG, and WEBP images are allowed.")
    
    max_size = 2 * 1024 * 1024
    if value.size > max_size:
        raise serializers.ValidationError("Image size must not exceed 2MB.")
    
    return value

def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', value):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', value):
        raise serializers.ValidationError("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return value

def validate_phone_number(value):
    if len(value) < 14:
        raise serializers.ValidationError("Phone number must be at least 14 characters long.")
    if len(value) > 14:
        raise serializers.ValidationError("Phone number must not exceed 14 characters.")
    if re.search(r'[A-Z]', value) or re.search(r'[a-z]', value) or re.search(r'[!@#$_%^&*(),.?":{}|<>\-]', value):
        raise serializers.ValidationError("Phone number contains an invalid character.")
    return value


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    profile_picture = serializers.ImageField(validators=[validate_image], required=False)


    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number', 'profile_picture', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def validate_password(self, value):
        return validate_password_strength(value)
    
    def validate_phone_number(self, value):
        return validate_phone_number(value)

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # token info
        access_token = AccessToken.for_user(self.user)
        data['token_info'] = {
            'issued_at': access_token['iat'],
            'expires_at': access_token['exp'],
        }

        # user data
        data['user'] = {
            'user_id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'phone_number': self.user.phone_number,
        }

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(validators=[validate_image], required=False)

    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number', 'profile_picture']
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False},
        }
    
    def validate_phone_number(self, value):
        return validate_phone_number(value)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_password(self, value):
        return validate_password_strength(value)


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(validators=[validate_image], required=False)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'category_name', 'image']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name',]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']
