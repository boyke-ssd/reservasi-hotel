from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('hotels/', views.HotelListView.as_view(), name='hotel_list'),
    path('hotel/search/', views.HotelSearchView.as_view(), name='hotel_search'),
    path('hotel/<int:hotel_id>/', views.HotelDetailView.as_view(), name='hotel_detail'),
    # Pastikan URL dengan parameter dinamis (hotel_id) didefinisikan sebelum URL statis
    path('reservation/<int:hotel_id>/', views.ReservationView.as_view(), name='reservation_form'),
    path('reservation/', views.ReservationView.as_view(), name='reservation'),
    path('reservation/<int:reservation_id>/payment/', views.PaymentView.as_view(), name='payment'),
    path('reservation/<int:reservation_id>/detail/', views.ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservation/<int:reservation_id>/cancel/', views.CancelReservationView.as_view(), name='cancel_reservation'),
    path('reservation/history/', views.ReservationHistoryView.as_view(), name='reservation_history'),
    path('reservation/<int:reservation_id>/review/', views.ReviewView.as_view(), name='review'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('about/', views.AboutView.as_view(), name='about'),
]