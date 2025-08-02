from django.views.generic import TemplateView, FormView, View, ListView
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm, ReservationForm, PaymentForm, ReviewForm
from .models import Hotel, HotelGallery, Room, Reservation, Payment, Review, UserProfile, Facility
from django.db.models import Q
from datetime import date, datetime
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from decimal import Decimal
from functools import reduce

# Mixin untuk memeriksa login
class AppLoginRequiredMixin(LoginRequiredMixin):
    login_url = reverse_lazy('login')

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

# Registrasi
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
            address=''
        )
        
        subject = 'Selamat Datang di Hotel Djangoo'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        context = {
            'first_name': user.first_name or user.username,
            'email': user.email,
            'tanggal_daftar': user.date_joined.strftime('%d %B %Y') if hasattr(user, 'date_joined') else 'Hari ini'
        }
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = f"Halo {user.first_name or user.username}, akun Anda berhasil dibuat."
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        
        try:
            msg.send()
            messages.success(self.request, 'Registrasi berhasil! Cek email Anda.')
        except Exception as e:
            messages.warning(self.request, f'Registrasi berhasil, tapi gagal mengirim email: {str(e)}')
        
        return super().form_valid(form)

# Login
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['app_auth'] = {'user_id': self.request.user.id}
        return response

    def get_success_url(self):
        return reverse_lazy('home')

# Logout
class CustomLogoutView(View):
    def get(self, request):
        if 'app_auth' in request.session:
            del request.session['app_auth']
        request.session.flush()
        return redirect('home')

# Daftar hotel
class HotelListView(TemplateView):
    template_name = 'hotel/hotel_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotels = Hotel.objects.all().prefetch_related('room_types', 'gallery')
        hotel_data = []

        for hotel in hotels:
            gambar = hotel.gallery.first()
            room_types = hotel.room_types.all()
            harga_termurah = min([rt.base_price for rt in room_types], default=0)
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
    template_name = 'hotel/hotel_search.html'

    def get(self, request):
        hotels = Hotel.objects.all().prefetch_related('room_types', 'gallery')
        destination_id = request.GET.get('destination_id')
        star_ratings = request.GET.getlist('star_rating')

        hotel_data = []

        if destination_id:
            hotel = Hotel.objects.filter(id=destination_id).first()
            if hotel and hotel.region:
                hotels = hotels.filter(region=hotel.region)

        if star_ratings:
            try:
                star_ratings = [int(rating) for rating in star_ratings if rating]
                if star_ratings:
                    hotels = hotels.filter(reduce(lambda x, y: x | y, [Q(star_rating=rating) for rating in star_ratings]))
            except ValueError:
                pass

        for hotel in hotels:
            gambar = hotel.gallery.first()
            room_types = hotel.room_types.all()
            harga_termurah = min([rt.base_price for rt in room_types], default=0)
            jumlah_ulasan = Review.objects.filter(reservation__room__hotel=hotel).count()

            hotel_data.append({
                'obj': hotel,
                'image': gambar.image.url if gambar else None,
                'harga_termurah': harga_termurah,
                'jumlah_ulasan': jumlah_ulasan,
            })

        return render(request, self.template_name, {
            'hotel_data': hotel_data,
            'all_hotels': Hotel.objects.all()
        })

# Detail hotel
class HotelDetailView(TemplateView):
    template_name = 'hotel/hotel_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel_id = self.kwargs['hotel_id']
        hotel = get_object_or_404(Hotel, pk=hotel_id)

        gallery = HotelGallery.objects.filter(hotel_id=hotel_id)
        rooms = Room.objects.filter(hotel=hotel, is_available=True).select_related('room_type')
        reviews = Review.objects.filter(reservation__room__hotel=hotel)

        harga_list = [
            r.room_type.base_price
            for r in rooms
            if r.room_type and r.room_type.base_price is not None
        ]
        harga_termurah = min(harga_list) if harga_list else 0

        facilities = Facility.objects.filter(room__in=rooms).distinct()

        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')

        context.update({
            'hotel': hotel,
            'gallery': gallery,
            'rooms': rooms,
            'facilities': facilities,
            'reviews': reviews,
            'harga_termurah': harga_termurah,
            'check_in': check_in,
            'check_out': check_out,
        })

        return context

# Reservasi
class ReservationView(AppLoginRequiredMixin, View):
    form_template_name = 'reservasi/reservasi.html'
    list_template_name = 'reservasi/list_reservasi.html'
    TAX_RATE = Decimal('0.10')

    def get(self, request, hotel_id=None):
        if hotel_id:
            # Tampilkan form reservasi
            hotel = get_object_or_404(Hotel, pk=hotel_id)
            rooms = Room.objects.filter(hotel=hotel, is_available=True).select_related('room_type')
            check_in = request.GET.get('check_in') 
            check_out = request.GET.get('check_out') 
            if not check_in or check_in.lower() == 'none':
                check_in = date.today().strftime('%Y-%m-%d')

            if not check_out or check_out.lower() == 'none':
                check_out = (date.today() + timezone.timedelta(days=1)).strftime('%Y-%m-%d')
                
            room_id = request.GET.get('room_id')
            room = Room.objects.filter(pk=room_id).first() if room_id else rooms.first() if rooms.exists() else None

            harga_kamar = Decimal(room.room_type.base_price) if room else Decimal(0)
            durasi = 1
            total_kamar = harga_kamar
            pajak = Decimal(0)
            total_harga = total_kamar

            if check_in and check_out:
                try:
                    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
                    check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
                    if check_out_date > check_in_date:
                        durasi = (check_out_date - check_in_date).days
                        total_kamar = harga_kamar * durasi
                        pajak = total_kamar * self.TAX_RATE
                        total_harga = total_kamar + pajak
                except (ValueError, TypeError):
                    pass

            form = ReservationForm(
                hotel_id=hotel_id,
                initial={
                    'room': room.id if room else None,
                    'check_in': check_in,
                    'check_out': check_out,
                    'first_name': request.user.first_name or '',
                    'last_name': request.user.last_name or '',
                    'email': request.user.email or '',
                    'phone': request.user.profile.phone if hasattr(request.user, 'profile') else ''
                }
            )

            return render(request, self.form_template_name, {
                'form': form,
                'hotel': hotel,
                'rooms': rooms,
                'room_obj': room,
                'harga_kamar': harga_kamar,
                'durasi': durasi,
                'total_kamar': total_kamar,
                'pajak': pajak,
                'total_harga': total_harga,
                'check_in': check_in,  
                'check_out': check_out  
            })
        else:
            # Tampilkan daftar reservasi
            reservations = Reservation.objects.filter(
                user=request.user,
                status__in=['PENDING', 'PAID', 'CHECKED_IN']
            ).order_by('-check_in')
            return render(request, self.list_template_name, {
                'reservations': reservations,
            })

    def post(self, request, hotel_id):
        hotel = get_object_or_404(Hotel, pk=hotel_id)
        rooms = Room.objects.filter(hotel=hotel, is_available=True).select_related('room_type')
        form = ReservationForm(request.POST, hotel_id=hotel_id)

        room_id = request.POST.get('room')
        room = Room.objects.filter(pk=room_id).first() if room_id else None
        harga_kamar = Decimal(room.room_type.base_price) if room else Decimal(0)
        durasi = 1
        total_kamar = harga_kamar
        pajak = Decimal(0)
        total_harga = total_kamar

        # ✅ DEFINISIKAN DULU
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        check_in = None
        check_out = None

        if check_in_str and check_out_str:
            try:
                check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
                check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
                if check_out > check_in:
                    durasi = (check_out - check_in).days
                    total_kamar = harga_kamar * durasi
                    pajak = total_kamar * self.TAX_RATE
                    total_harga = total_kamar + pajak
            except (ValueError, TypeError):
                pass

        # ✅ SEKARANG BARU CEK form.is_valid()
        if form.is_valid():
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            if check_out > check_in:
                durasi = (check_out - check_in).days
                total_kamar = harga_kamar * durasi
                pajak = total_kamar * self.TAX_RATE
                total_harga = total_kamar + pajak

            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.hotel = hotel
            reservation.status = 'PENDING'  # atau status default kamu
            reservation.total_price = total_harga
            reservation.save()

            # 🔁 Redirect ke halaman pembayaran
            return redirect('payment', reservation_id=reservation.id)  # Redirect ke halaman pembayaran

        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        if check_in_str and check_out_str:
            try:
                check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
                check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()
                if check_out_date > check_in_date:
                    durasi = (check_out_date - check_in_date).days
                    total_kamar = harga_kamar * durasi
                    pajak = total_kamar * self.TAX_RATE
                    total_harga = total_kamar + pajak
            except (ValueError, TypeError):
                pass

        return render(request, self.form_template_name, {
            'form': form,
            'hotel': hotel,
            'rooms': rooms,
            'room_obj': room,
            'harga_kamar': harga_kamar,
            'durasi': durasi,
            'total_kamar': total_kamar,
            'pajak': pajak,
            'total_harga': total_harga,
            'check_in': check_in,  
            'check_out': check_out 
        })

# Pembayaran
class PaymentView(AppLoginRequiredMixin, View):
    template_name = 'payment/payment.html'

    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        form = PaymentForm()
        payment_details = {
            'bank_transfer': [
                {'bank': 'BCA', 'account_number': '1234567890', 'account_name': 'Hotel Djangoo'},
                {'bank': 'Mandiri', 'account_number': '0987654321', 'account_name': 'Hotel Djangoo'},
            ],
            'e_wallet': [
                {'provider': 'OVO', 'number': '081234567890'},
                {'provider': 'DANA', 'number': '081987654321'},
                {'provider': 'GoPay', 'number': '082345678901'},
            ],
        }
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation,
            'payment_details': payment_details,
        })

    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.reservation = reservation
            payment.is_paid = False
            payment.paid_at = None
            payment.save()
            reservation.status = 'PENDING'
            reservation.save()
            messages.success(request, 'Pembayaran berhasil! Tunggu Reservasi Anda dikonfirmasi.')
            return redirect('reservation')  # Redirect ke daftar reservasi
        payment_details = {
            'bank_transfer': [
                {'bank': 'BCA', 'account_number': '1234567890', 'account_name': 'Hotel Djangoo'},
                {'bank': 'Mandiri', 'account_number': '0987654321', 'account_name': 'Hotel Djangoo'},
            ],
            'e_wallet': [
                {'provider': 'OVO', 'number': '081234567890'},
                {'provider': 'DANA', 'number': '081987654321'},
                {'provider': 'GoPay', 'number': '082345678901'},
            ],
        }
        return render(request, self.template_name, {
            'form': form,
            'reservation': reservation,
            'payment_details': payment_details,
        })

# Detail Reservasi
class ReservationDetailView(AppLoginRequiredMixin, View):
    template_name = 'reservasi/detail_reservasi.html'

    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        return render(request, self.template_name, {
            'reservation': reservation,
        })

# Pembatalan reservasi
class CancelReservationView(AppLoginRequiredMixin, View):
    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        if reservation.status in ['PENDING', 'PAID']:
            reservation.status = 'CANCELLED'
            reservation.save()
            messages.success(request, 'Reservasi berhasil dibatalkan.')
        else:
            messages.error(request, 'Reservasi tidak dapat dibatalkan.')
        return redirect('reservation_history')

# Riwayat reservasi
class ReservationHistoryView(AppLoginRequiredMixin, TemplateView):
    template_name = 'riwayat/riwayat_reservasi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        context['reservations'] = Reservation.objects.filter(
            user=self.request.user,
            status__in=['CHECKED_OUT', 'CANCELLED']
        ).filter(
            Q(status='CHECKED_OUT', check_out__lt=today) | Q(status='CANCELLED')
        ).order_by('-check_out')
        return context

# Ulasan
class ReviewView(AppLoginRequiredMixin, View):
    template_name = 'review/review.html'

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