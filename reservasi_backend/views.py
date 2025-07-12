from django.views.generic import TemplateView, FormView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm, ReservationForm, PaymentForm, ReviewForm
from .models import Hotel, HotelGallery, Room, Reservation, Payment, Review, UserProfile, Review, Facility
from django.db.models import Q
from datetime import date, datetime
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import AccessMixin
from django.utils import timezone
from decimal import Decimal

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
        hotels = Hotel.objects.all().prefetch_related('room_types', 'gallery')
        hotel_data = []

        for hotel in hotels:
            # Ambil gambar pertama
            gambar = hotel.gallery.first()

            # Ambil harga termurah
            room_types = hotel.room_types.all()
            harga_termurah = min([rt.base_price for rt in room_types], default=None)

            # Ambil jumlah ulasan
            jumlah_ulasan = Review.objects.filter(reservation__room__hotel=hotel).count()

            hotel_data.append({
                'obj': hotel,
                'image': gambar.image.url if gambar else None,
                'harga_termurah': harga_termurah,
                'jumlah_ulasan': jumlah_ulasan,
            })

        context['hotel_data'] = hotel_data
        context['all_hotels'] = hotels
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

        gallery = HotelGallery.objects.filter(hotel=hotel_id)
        rooms = Room.objects.filter(hotel=hotel, is_available=True).select_related('room_type')
        reviews = Review.objects.filter(reservation__room__hotel=hotel)

        # Harga termurah
        harga_list = [
            r.room_type.base_price
            for r in rooms
            if r.room_type and r.room_type.base_price is not None
        ]
        harga_termurah = min(harga_list) if harga_list else None
        context['harga_termurah'] = harga_termurah

        # Ambil semua kamar hotel ini
        rooms = Room.objects.filter(hotel=hotel, is_available=True).prefetch_related('facilities')
        
        # Kumpulkan semua fasilitas dari kamar-kamar hotel tersebut
        fasilitas_set = Facility.objects.filter(room__in=rooms).distinct()

        # Ambil checkin/checkout dari URL query parameter
        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')

        context.update({
            'hotel': hotel,
            'gallery': gallery,
            'rooms': rooms,
            'facilities': fasilitas_set,
            'reviews': reviews,
            'harga_termurah': harga_termurah,
            'check_in': check_in,
            'check_out': check_out,
            
        })

        return context

# Reservasi
class ReservationView(AppLoginRequiredMixin, View):
    template_name = 'reservasi/reservasi.html'
    login_url = reverse_lazy('login')
    TAX_RATE = Decimal('0.10')  # 10%

    def get(self, request, hotel_id=None):
        hotel = get_object_or_404(Hotel, pk=hotel_id) if hotel_id else None
        rooms = Room.objects.filter(hotel=hotel, is_available=True)

        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        room_id = request.GET.get('room_id')

        room_obj = Room.objects.filter(pk=room_id).first() if room_id else rooms.first()

        harga_kamar = Decimal(room_obj.room_type.base_price) if room_obj else Decimal(0)
        durasi = 1
        total_kamar = harga_kamar
        pajak = Decimal(0)
        total_harga = total_kamar

        if check_in and check_out:
            try:
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
                durasi = max((check_out_date - check_in_date).days, 1)
                total_kamar = harga_kamar * durasi
                pajak = total_kamar * self.TAX_RATE
                total_harga = total_kamar + pajak
            except:
                pass

        form = ReservationForm(
            hotel_id=hotel_id,
            initial={
                'check_in': check_in,
                'check_out': check_out,
                'room': room_obj.id if room_obj else None
            }
        )

        return render(request, self.template_name, {
            'form': form,
            'hotel': hotel,
            'rooms': rooms,
            'room_obj': room_obj,
            'harga_kamar': harga_kamar,
            'durasi': durasi,
            'total_kamar': total_kamar,
            'pajak': pajak,
            'total_harga': total_harga,
        })

    def post(self, request, hotel_id=None):
        form = ReservationForm(request.POST, hotel_id=hotel_id)
        hotel = get_object_or_404(Hotel, pk=hotel_id)
        rooms = Room.objects.filter(hotel=hotel, is_available=True)

        room_id = request.POST.get("room")
        room_obj = Room.objects.filter(pk=room_id).first()

        harga_kamar = Decimal(room_obj.room_type.base_price) if room_obj else Decimal(0)
        durasi = 1
        total_kamar = Decimal(0)
        pajak = Decimal(0)
        total_harga = Decimal(0)

        try:
            check_in = datetime.strptime(request.POST.get("check_in"), "%Y-%m-%d").date()
            check_out = datetime.strptime(request.POST.get("check_out"), "%Y-%m-%d").date()
            durasi = max((check_out - check_in).days, 1)
            total_kamar = harga_kamar * durasi
            pajak = total_kamar * self.TAX_RATE
            total_harga = total_kamar + pajak
        except:
            pass

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.total_price = total_harga
            reservation.save()
            return redirect('payment', reservation_id=reservation.id)

        return render(request, self.template_name, {
            'form': form,
            'hotel': hotel,
            'rooms': rooms,
            'room_obj': room_obj,
            'harga_kamar': harga_kamar,
            'durasi': durasi,
            'total_kamar': total_kamar,
            'pajak': pajak,
            'total_harga': total_harga,
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