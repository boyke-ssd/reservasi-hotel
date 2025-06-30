from django.urls import path
from . import views

urlpatterns = [
    path('', views.halaman_awal, name='home'),
    
    #halaman autentifikasi
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    #navbar 
    path('tipe-kamar/', views.tipe_kamar_list, name='tipe_kamar_list'),
    path('fasilitas/', views.fasilitas_list, name='fasilitas_list'),
    path('ulasan/', views.ulasan_list, name='ulasan_list'),
    path('tim/', views.team_view, name='tim'),

    path('booking/', views.booking, name='booking'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    
]
