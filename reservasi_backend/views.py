from django.views.generic import TemplateView, FormView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm, ReservationForm, PaymentForm, ReviewForm
from .models import Hotel, HotelGallery, Room, Reservation, Payment, Review, UserProfile
from django.db.models import Q
from datetime import date
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import AccessMixin
from django.utils import timezone

# Mixin untuk memeriksa sesi aplikasi
class AppLoginRequiredMixin(AccessMixin):
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if 'app_auth' not in request.session or 'user_id' not in request.session['app_auth']:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

# Beranda publik
class HomeView(TemplateView):
    template_name = 'beranda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hotels'] = Hotel.objects.all()[:3]
        context['featured_hotel'] = Hotel.objects.first()
        context['gallery'] = HotelGallery.objects.filter(hotel=context['featured_hotel'])[:6] if context['featured_hotel'] else []
        context['all_hotels'] = Hotel.objects.all()
        if context['featured_hotel'] and not context['featured_hotel'].location:
            context['featured_hotel'].location = "Lokasi tidak tersedia"
        return context

# Register
class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        UserProfile.objects.create(
            user=user,
            phone=form.cleaned_data['phone'],
            gender=form.cleaned_data['gender'],
            address=''  # Kosong karena tidak wajib di form
        )
        # Kirim email selamat datang
        subject = 'Selamat Datang di Hotel Djangoo – Pendaftaran Berhasil!'
        from_email = 'admin@hoteldjangoo.com'
        to_email = [user.email]
        context = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'tanggal_daftar': user.date_joined.strftime('%d %B %Y') if hasattr(user, 'date_joined') else 'Hari ini'
        }
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = f"Halo {user.first_name}, akun Anda berhasil dibuat."
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return super().form_valid(form)

# Login
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        # Autentikasi pengguna tanpa memanggil login()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            # Simpan user_id di namespace app_auth
            self.request.session['app_auth'] = {'user_id': user.id}
            self.request.session.modified = True
            return redirect(self.get_success_url())
        else:
            form.add_error(None, "Username atau password salah.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('home')

# Logout
class CustomLogoutView(View):
    def get(self, request):
        # Hapus sesi aplikasi
        if 'app_auth' in request.session:
            del request.session['app_auth']
        return redirect('home')

# Daftar hotel
class HotelListView(TemplateView):
    template_name = 'hotel/hotel_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hotels'] = Hotel.objects.all()
        return context

# Pencarian hotel
class HotelSearchView(View):
    template_name = 'hotel/hotel_list.html'

    def get(self, request):
        query = request.GET.get('destination', '')
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        hotels = Hotel.objects.all()
        if query:
            hotels = hotels.filter(
                Q(name__icontains=query) | Q(location__icontains=query)
            )
        if check_in and check_out:
            try:
                check_in_date = date.fromisoformat(check_in)
                check_out_date = date.fromisoformat(check_out)
                available_rooms = Room.objects.filter(
                    is_available=True
                ).exclude(
                    reservations__check_in__lt=check_out_date,
                    reservations__check_out__gt=check_in_date,
                    reservations__status__in=['PENDING', 'PAID', 'CHECKED_IN']
                )
                hotels = hotels.filter(rooms__in=available_rooms).distinct()
            except ValueError:
                pass
        return render(request, self.template_name, {'hotels': hotels})

# Detail hotel
class HotelDetailView(TemplateView):
    template_name = 'hotel/hotel_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel_id = self.kwargs['hotel_id']
        hotel = get_object_or_404(Hotel, pk=hotel_id)
        context['hotel'] = hotel
        context['gallery'] = HotelGallery.objects.filter(hotel=hotel_id)
        context['rooms'] = Room.objects.filter(hotel=hotel, is_available=True)
        context['reviews'] = Review.objects.filter(reservation__room__hotel=hotel)
        return context

# Reservasi
class ReservationView(AppLoginRequiredMixin, View):
    template_name = 'reservasi/reservasi.html'
    login_url = reverse_lazy('login')

    def get(self, request, hotel_id=None):
        hotel = get_object_or_404(Hotel, pk=hotel_id) if hotel_id else None
        rooms = Room.objects.filter(hotel=hotel, is_available=True) if hotel else Room.objects.filter(is_available=True)
        form = ReservationForm(hotel_id=hotel_id, initial={'room': rooms.first() if rooms.exists() else None})
        return render(request, self.template_name, {
            'form': form,
            'hotel': hotel,
            'rooms': rooms
        })

    def post(self, request, hotel_id=None):
        form = ReservationForm(request.POST, hotel_id=hotel_id)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.calculate_total_price()
            reservation.save()
            return redirect('payment', reservation_id=reservation.id)
        hotel = get_object_or_404(Hotel, pk=hotel_id) if hotel_id else None
        rooms = Room.objects.filter(hotel=hotel, is_available=True) if hotel else Room.objects.filter(is_available=True)
        return render(request, self.template_name, {
            'form': form,
            'hotel': hotel,
            'rooms': rooms
        })

# Pembayaran
class PaymentView(AppLoginRequiredMixin, View):
    template_name = 'payment/payment.html'
    login_url = reverse_lazy('login')

    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        form = PaymentForm()
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation
        })

    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.reservation = reservation
            payment.is_paid = True
            payment.paid_at = timezone.now()
            payment.save()
            reservation.status = 'PAID'
            reservation.save()
            return redirect('reservation_history')
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation
        })

# Pembatalan reservasi
class CancelReservationView(AppLoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        if reservation.status in ['PENDING', 'PAID']:
            reservation.status = 'CANCELLED'
            reservation.save()
        return redirect('reservation_history')

# Riwayat reservasi
class ReservationHistoryView(AppLoginRequiredMixin, TemplateView):
    template_name = 'riwayat/riwayat_reservasi.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = Reservation.objects.filter(user=self.request.user)
        return context

# Ulasan
class ReviewView(AppLoginRequiredMixin, View):
    template_name = 'review/review.html'
    login_url = reverse_lazy('login')

    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user, status='CHECKED_OUT')
        form = ReviewForm()
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation
        })

    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user, status='CHECKED_OUT')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reservation = reservation
            review.save()
            return redirect('reservation_history')
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation
        })

# Tentang kami
class AboutView(TemplateView):
    template_name = 'about/tentang_kami.html'