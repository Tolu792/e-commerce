from django.urls import path, include
from .views import (RegisterUserView, CustomTokenObtainPairView, UserProfileView, ChangePasswordView,
                    ProductViewSet, CategoryViewSet, CartViewSet, OrderViewSet)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('products', ProductViewSet, basename='products')
router.register('category', CategoryViewSet, basename='category')
router.register('cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
