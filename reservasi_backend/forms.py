from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Room, Reservation, Payment, Review
from captcha.fields import CaptchaField
from django.utils import timezone

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=True)
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError("Nomor telepon hanya boleh berisi angka.")
        return phone

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name')
        if any(char in name for char in "<>{}[]/\\|&$"):
            raise forms.ValidationError("Nama tidak boleh mengandung karakter aneh.")
        return name

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, hotel_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hotel_id:
            self.fields['room'].queryset = Room.objects.filter(hotel_id=hotel_id, is_available=True)

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        room = cleaned_data.get('room')
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Tanggal check-out harus setelah check-in.")
        if room and check_in and check_out:
            if Reservation.objects.filter(
                room=room,
                check_in__lte=check_out,
                check_out__gte=check_in,
                status__in=['PENDING', 'PAID', 'CHECKED_IN']
            ).exists():
                raise forms.ValidationError("Kamar sudah dipesan untuk tanggal tersebut.")

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'proof']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not (1 <= rating <= 5):
            raise forms.ValidationError("Rating harus antara 1 dan 5.")
        return rating