from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ======================
# User Profile
# ======================
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', _('Laki-laki')),
        ('F', _('Perempuan')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("Pengguna"))
    phone = models.CharField(max_length=20, verbose_name=_("Nomor Telepon"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Jenis Kelamin"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Alamat"))

    class Meta:
        verbose_name = _("Profil Pengguna")
        verbose_name_plural = _("Profil Pengguna")

    def __str__(self):
        return self.user.username

class Hotel(models.Model):
    facilities = models.ManyToManyField('Facility', related_name='hotels', blank=True, verbose_name=_("Fasilitas"))
    name = models.CharField(max_length=200, verbose_name=_("Nama Hotel"))
    description = models.TextField(blank=True, verbose_name=_("Deskripsi"))
    address = models.TextField(verbose_name=_("Alamat"))
    city = models.CharField(max_length=100, verbose_name=_("Kota"))
    province = models.CharField(max_length=100, verbose_name=_("Provinsi"))
    rating = models.PositiveSmallIntegerField(default=0, verbose_name=_("Rating (1-5)"))
    image_cover = models.ImageField(upload_to='hotels/', blank=True, null=True, verbose_name=_("Gambar Utama"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotel")

    def __str__(self):
        return self.name

class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="images", verbose_name=_("Hotel"))
    image = models.ImageField(upload_to='hotel_images/', verbose_name=_("Gambar"))
    caption = models.CharField(max_length=200, blank=True, verbose_name=_("Keterangan"))

    class Meta:
        verbose_name = _("Gambar Hotel")
        verbose_name_plural = _("Gambar Hotel")

    def __str__(self):
        return f"Gambar {self.hotel.name}"

# ======================
# Tipe Kamar
# ======================
class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, verbose_name=_("Hotel"))
    name = models.CharField(max_length=100, verbose_name=_("Nama Tipe Kamar"))
    description = models.TextField(blank=True, verbose_name=_("Deskripsi"))
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Harga per Malam"))
    image = models.ImageField(upload_to='room_types/', null=True, blank=True)

    class Meta:
        verbose_name = _("Tipe Kamar")
        verbose_name_plural = _("Tipe Kamar")

    def __str__(self):
        return self.name


# ======================
# Fasilitas Kamar
# ======================
class Facility(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nama Fasilitas"))
    icon = models.CharField(max_length=100, blank=True, verbose_name=_("Ikon (Opsional)"))

    class Meta:
        verbose_name = _("Fasilitas")
        verbose_name_plural = _("Fasilitas")

    def __str__(self):
        return self.name


# ======================
# Kamar
# ======================
class Room(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name=_("Nomor Kamar"))
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, verbose_name=_("Tipe Kamar"))
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, verbose_name=_("Hotel"), null=True)
    facilities = models.ManyToManyField(Facility, blank=True, verbose_name=_("Fasilitas"))
    is_available = models.BooleanField(default=True, verbose_name=_("Tersedia"))


    class Meta:
        verbose_name = _("Kamar")
        verbose_name_plural = _("Kamar")

    def __str__(self):
        return f"Kamar {self.number} - {self.room_type.name}"


# ======================
# Reservasi
# ======================
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Pemesan"))
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name=_("Kamar"))
    check_in = models.DateField(verbose_name=_("Tanggal Check-in"))
    check_out = models.DateField(verbose_name=_("Tanggal Check-out"))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total Harga"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Dipesan Pada"))

    class Meta:
        verbose_name = _("Reservasi")
        verbose_name_plural = _("Reservasi")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.room.number} ({self.check_in} - {self.check_out})"

    def duration(self):
        return (self.check_out - self.check_in).days


# ======================
# Pembayaran
# ======================
class Payment(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, verbose_name=_("Reservasi"))
    method = models.CharField(max_length=50, verbose_name=_("Metode Pembayaran"))
    is_paid = models.BooleanField(default=False, verbose_name=_("Lunas"))
    proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, verbose_name=_("Bukti Pembayaran"))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Dibayar Pada"))

    class Meta:
        verbose_name = _("Pembayaran")
        verbose_name_plural = _("Pembayaran")

    def __str__(self):
        return f"Pembayaran #{self.reservation.id} - {'Lunas' if self.is_paid else 'Belum Lunas'}"


# ======================
# Ulasan / Review
# ======================
class Review(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, verbose_name=_("Reservasi"))
    rating = models.PositiveSmallIntegerField(verbose_name=_("Rating (1-5)"))
    comment = models.TextField(blank=True, verbose_name=_("Komentar"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Tanggal Ulasan"))

    class Meta:
        verbose_name = _("Ulasan")
        verbose_name_plural = _("Ulasan")

    def __str__(self):
        return f"Ulasan {self.reservation.room.number} oleh {self.reservation.user.username}"
