from django.urls import path
from .import views
from .views import RegisterUserView

urlpatterns = [
    path('users/', views.CustomUserList.as_view()),
    path('users/<int:pk>/', views.CustomUserDetail.as_view()),
    path('register/', RegisterUserView.as_view()),

]