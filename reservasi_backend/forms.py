from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Reservation, Payment, Review, Room
from django.utils import timezone

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=15, required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'phone', 'gender']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email sudah digunakan.")
        return email

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'check_in', 'check_out', 'first_name', 'last_name', 'email', 'phone', 'special_request']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
            'special_request': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        hotel_id = kwargs.pop('hotel_id', None)
        super().__init__(*args, **kwargs)
        if hotel_id:
            self.fields['room'].queryset = Room.objects.filter(hotel_id=hotel_id, is_available=True)

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError("Tanggal check-out harus setelah check-in.")
            if check_in < timezone.now().date():
                raise forms.ValidationError("Tanggal check-in tidak boleh di masa lalu.")
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'proof']
        widgets = {
            'method': forms.Select(choices=[
                ('BANK_TRANSFER', 'Transfer Bank'),
                ('E_WALLET', 'Dompet Digital'),
            ]),
            'proof': forms.FileInput(),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }