from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

# Fungsi default untuk ForeignKey
def get_default_hotel():
    return Hotel.objects.first().id if Hotel.objects.exists() else None

# ======================
# Profil Pengguna
# ======================
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', _('Laki-laki')),
        ('F', _('Perempuan')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Pengguna"),
        related_name='profile'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Nomor Telepon")
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='M',
        verbose_name=_("Jenis Kelamin")
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Alamat")
    )

    class Meta:
        verbose_name = _("Profil Pengguna")
        verbose_name_plural = _("Profil Pengguna")

    def __str__(self):
        return self.user.username

    def clean(self):
        if self.phone and not self.phone.isdigit():
            raise ValidationError(_("Nomor telepon harus berupa angka."))

# ======================
# Hotel
# ======================
class Hotel(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nama Hotel")
    )
    location = models.CharField(
        max_length=200,
        verbose_name=_("Lokasi")
    )
    region = models.CharField(
        max_length=200,
        choices=[
            ('Lampung', 'Lampung'),
            ('Jakarta', 'Jakarta'),
            ('Surabaya', 'Surabaya'),
            ('Bandung', 'Bandung'),
            ('Sumatra Barat', 'Sumatra Barat'),
            ('Balikpapan', 'Bali'),
            ('Jawa Barat', 'Jawa Barat'),
            ('Jawa Timur', 'Jawa Timur'),
            ('Balikpapan', 'Balikpapan'),
        ],
        verbose_name=_("Region")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Deskripsi")
    )
    average_rating = models.FloatField(
        default=0.0,
        verbose_name=_("Rating Rata-rata")
    )
    star_rating = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_("Rating Bintang (0-5)")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Dibuat Pada")
    )

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotel")

    def __str__(self):
        return self.name

    def update_average_rating(self):
        from django.db.models import Avg
        reviews = Review.objects.filter(reservation__room__hotel=self)
        if reviews.exists():
            self.average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        else:
            self.average_rating = 0.0
        self.save()

# ======================
# Galeri Hotel
# ======================
class HotelGallery(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        related_name='gallery',
        on_delete=models.CASCADE,
        verbose_name=_("Hotel")
    )
    image = models.ImageField(
        upload_to='hotel_images/',
        verbose_name=_("Gambar")
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Keterangan")
    )

    class Meta:
        verbose_name = _("Galeri Hotel")
        verbose_name_plural = _("Galeri Hotel")

    def __str__(self):
        return f"Gambar untuk {self.hotel.name}"

# ======================
# Tipe Kamar
# ======================
class RoomType(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        related_name='room_types',
        on_delete=models.CASCADE,
        verbose_name=_("Hotel")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nama Tipe Kamar")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Deskripsi")
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name=_("Harga per Malam")
    )

    class Meta:
        verbose_name = _("Tipe Kamar")
        verbose_name_plural = _("Tipe Kamar")

    def __str__(self):
        return f"{self.name} - {self.hotel.name}"

# ======================
# Fasilitas Kamar
# ======================
class Facility(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nama Fasilitas")
    )

    class Meta:
        verbose_name = _("Fasilitas")
        verbose_name_plural = _("Fasilitas")

    def __str__(self):
        return self.name

# ======================
# Kamar
# ======================
class Room(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        related_name='rooms',
        on_delete=models.CASCADE,
        verbose_name=_("Hotel")
    )
    number = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Nomor Kamar")
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        verbose_name=_("Tipe Kamar")
    )
    facilities = models.ManyToManyField(
        Facility,
        blank=True,
        verbose_name=_("Fasilitas")
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_("Tersedia")
    )

    class Meta:
        verbose_name = _("Kamar")
        verbose_name_plural = _("Kamar")

    def __str__(self):
        return f"Kamar {self.number} - {self.room_type.name} ({self.hotel.name})"

    def clean(self):
        if Room.objects.filter(hotel=self.hotel, number=self.number).exclude(pk=self.pk).exists():
            raise ValidationError(_("Nomor kamar sudah ada untuk hotel ini."))

# ======================
# Reservasi
# ======================
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', _('Menunggu Pembayaran')),
        ('PAID', _('Dibayar')),
        ('CHECKED_IN', _('Check-in')),
        ('CHECKED_OUT', _('Check-out')),
        ('CANCELLED', _('Dibatalkan')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Pemesan")
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Kamar")
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name=_("Nama Depan")
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name=_("Nama Belakang")
    )
    email = models.EmailField(
        verbose_name=_("Email"),
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_("Nomor Telepon"),
        null=True,
        blank=True
    )
    check_in = models.DateField(
        verbose_name=_("Tanggal Check-in")
    )
    check_out = models.DateField(
        verbose_name=_("Tanggal Check-out")
    )
    special_request = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Permintaan Khusus")
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Harga")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_("Status")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Dipesan Pada")
    )

    class Meta:
        verbose_name = _("Reservasi")
        verbose_name_plural = _("Reservasi")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.room.number} ({self.check_in} - {self.check_out})"

    def clean(self):
        if not self.check_in or not self.check_out:
            raise ValidationError(_("Tanggal check-in dan check-out harus diisi."))
        if self.check_out <= self.check_in:
            raise ValidationError(_("Tanggal check-out harus lebih besar dari tanggal check-in."))
        if self.room:
            overlapping_reservations = Reservation.objects.filter(
                room=self.room,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
                status__in=['PENDING', 'PAID', 'CHECKED_IN']
            ).exclude(pk=self.pk)
            if overlapping_reservations.exists():
                raise ValidationError(_("Kamar ini sudah dipesan untuk tanggal yang diminta."))
        if self.phone and not self.phone.isdigit():
            raise ValidationError(_("Nomor telepon harus berupa angka."))

    def duration(self):
        return (self.check_out - self.check_in).days

    def calculate_total_price(self):
        duration = self.duration()
        self.total_price = self.room.room_type.base_price * duration
        tax = self.total_price * Decimal('0.10')
        self.total_price += tax
        self.save()

# ======================
# Pembayaran
# ======================
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('BANK_TRANSFER', _('Transfer Bank')),
        ('E_WALLET', _('Dompet Digital')),
    ]

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        verbose_name=_("Reservasi")
    )
    method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        default='BANK_TRANSFER',
        verbose_name=_("Metode Pembayaran")
    )
    proof = models.ImageField(
        upload_to='payment_proofs/',
        blank=True,
        null=True,
        verbose_name=_("Bukti Pembayaran")
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name=_("Lunas")
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Dibayar Pada")
    )

    class Meta:
        verbose_name = _("Pembayaran")
        verbose_name_plural = _("Pembayaran")

    def __str__(self):
        return f"Pembayaran #{self.reservation.id} - {'Lunas' if self.is_paid else 'Belum Lunas'}"

# ======================
# Ulasan / Review
# ======================
class Review(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        verbose_name=_("Reservasi")
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating (1-5)")
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Komentar")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Tanggal Ulasan")
    )

    class Meta:
        verbose_name = _("Ulasan")
        verbose_name_plural = _("Ulasan")

    def __str__(self):
        return f"Ulasan {self.reservation.room.number} oleh {self.reservation.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reservation.room.hotel.update_average_rating()