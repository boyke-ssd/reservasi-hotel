from django.urls import path
from . import views

urlpatterns = [
    path('', views.halaman_awal, name='home'),
    path('', views.halaman_coba, name='coba'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('booking/', views.booking, name='booking'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
