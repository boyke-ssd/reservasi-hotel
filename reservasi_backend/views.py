from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm
from .models import UserProfile
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# Beranda publik
def halaman_awal(request):
    return render(request, "beranda.html")
def halaman_coba(request):
    return render(request, "coba.html")


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
