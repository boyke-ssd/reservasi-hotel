from django.urls import path
from . import views


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('hotels/', views.HotelListView.as_view(), name='hotel_list'),
    path('hotels/search/', views.HotelSearchView.as_view(), name='hotel_search'),
    path('hotels/<int:hotel_id>/', views.HotelDetailView.as_view(), name='hotel_detail'),
    path('reservation/', views.ReservationView.as_view(), name='reservation'),
    path('reservation/<int:hotel_id>/', views.ReservationView.as_view(), name='reservation_with_hotel'),
    path('payment/<int:reservation_id>/', views.PaymentView.as_view(), name='payment'),
    path('cancel/<int:reservation_id>/', views.CancelReservationView.as_view(), name='cancel_reservation'),
    path('history/', views.ReservationHistoryView.as_view(), name='reservation_history'),
    path('review/<int:reservation_id>/', views.ReviewView.as_view(), name='review'),
    path('about/', views.AboutView.as_view(), name='about'),
]