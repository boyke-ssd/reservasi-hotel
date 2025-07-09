from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, ReviewForm
from .models import UserProfile
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Min, F, ExpressionWrapper, FloatField
from .models import Hotel, RoomType, Room, Facility, HotelImage, Reservation, Review

# Beranda publik
def halaman_awal(request):
    daftar_hotel = Hotel.objects.prefetch_related('room_types', 'images')[:6]  # Batasi 6 hotel untuk beranda
    return render(request, "beranda.html", {'daftar_hotel': daftar_hotel})

# Register
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Kirim notifikasi email HTML
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

            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Arahkan sesuai peran
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')  # CUSTOMER ke halaman beranda
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


# Logout
def logout_view(request):
    logout(request)
    return redirect('home')


# Booking (hanya user biasa yang login)
@login_required
def booking(request):
    return render(request, 'booking/index.html')


# Dashboard admin
@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def admin_dashboard(request):
    return render(request, 'dashboard/index.html')

def hotel_list(request):
    daftar_hotel = (
        Hotel.objects
        .annotate(
            avg_rating = ExpressionWrapper(
                Avg('roomtype__room__reservation__review__rating') * 2.0,  # karena rating 0–5 dikalikan agar jadi 0–10
                output_field=FloatField()
            ),
            review_count = Count('roomtype__room__reservation__review', distinct=True),
            min_price = Min('roomtype__base_price'),
        )
        .prefetch_related('images')
    )
    return render(request, 'hotel/hotel_list.html', {
        'daftar_hotel': daftar_hotel
    })

def hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    tipe_kamar = RoomType.objects.filter(hotel=hotel).prefetch_related('room_set__facilities')
    fasilitas = hotel.facilities.all()
    gambar = hotel.images.all()
    
    return render(request, 'hotel/hotel_detail.html', {
        'hotel': hotel,
        'tipe_kamar': tipe_kamar,
        'fasilitas': fasilitas,
        'gambar': gambar
    })

# View untuk halaman daftar tipe kamar
def tipe_kamar_list(request):
    kamar_tersedia = Room.objects.filter(is_available=True).select_related('room_type__hotel').prefetch_related('facilities')
    return render(request, 'tipe_kamar/tipe_kamar_list.html', {'kamar_list': kamar_tersedia})
    
# View untuk halaman fasilitas
def fasilitas_list(request):
    return render(request, 'fasilitas/fasilitas_list.html')

# View untuk reservasi
def reservasi(request):
    return render(request, 'reservasi/reservasi.html')

# View untuk halaman tim
def team_view(request):
    return render(request, 'tim/tim.html')

# Detail kamar
def kamar_detail(request, pk):
    kamar = get_object_or_404(Room, pk=pk)
    return render(request, 'tipe_kamar/detail_kamar.html', {'kamar': kamar})

@login_required
def buat_ulasan(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.reservation = reservation
            ulasan.save()
            return redirect('reservasi_saya')  # misal
    else:
        form = ReviewForm()
    return render(request, 'review/form_ulasan.html', {'form': form})
