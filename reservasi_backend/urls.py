from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.halaman_awal, name='home'),
    
    # halaman autentifikasi
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # navbar 
    path('kamar/', views.tipe_kamar_list, name='kamar'),
    path('fasilitas/', views.fasilitas_list, name='fasilitas_list'),
    path('reservasi/', views.reservasi, name='reservasi'),
    path('tim/', views.team_view, name='tim'),

    path('booking/', views.booking, name='booking'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # kamar
    path('kamar/<int:pk>/', views.kamar_detail, name='kamar_detail'),

    # hotel
    path('hotel/', views.hotel_list, name='hotel_list'),
    path('hotel/<int:pk>/', views.hotel_detail, name='hotel_detail'),

    path('ulasan/<int:reservation_id>/', views.buat_ulasan, name='buat_ulasan'),

]
