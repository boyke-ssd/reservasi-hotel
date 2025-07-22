from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Hotel, HotelGallery, RoomType, Facility, Room, Reservation, Payment, Review

# ======================
# Inline Definitions
# ======================
class HotelGalleryInline(admin.TabularInline):
    model = HotelGallery
    extra = 1
    fields = ['image', 'caption']
    readonly_fields = []
    can_delete = True

class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 1
    fields = ['name', 'description', 'base_price']
    readonly_fields = []
    can_delete = True

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = ['number', 'room_type', 'is_available', 'facilities']
    filter_horizontal = ['facilities']
    readonly_fields = []
    can_delete = True

class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    fields = ['method', 'is_paid', 'proof', 'paid_at']
    readonly_fields = ['paid_at']
    can_delete = False

class ReviewInline(admin.StackedInline):
    model = Review
    extra = 0
    fields = ['rating', 'comment', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ['phone', 'gender', 'address']
    extra = 0

# ====================
# Menyesuaikan UserAdmin Bawaan
# ====================
admin.site.unregister(User)  # Hapus pendaftaran bawaan User
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser', 'groups']

admin.site.register(User, CustomUserAdmin)  # Daftarkan kembali dengan kustomisasi

# ====================
# UserProfile Admin
# ====================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'phone', 'gender', 'address']
    search_fields = ['user__username', 'user__email', 'phone', 'address']
    list_filter = ['gender']

    def username(self, obj):
        return obj.user.username
    username.short_description = _("Nama Pengguna")

# ====================
# Hotel Admin
# ====================
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'region', 'average_rating', 'star_rating','created_at']
    search_fields = ['name', 'location', 'description', 'region']
    list_filter = ['created_at', 'region']  # Tambahkan filter berdasarkan region
    inlines = [HotelGalleryInline, RoomTypeInline]
    readonly_fields = ['created_at', 'average_rating']
    actions = ['update_average_rating']

    def update_average_rating(self, request, queryset):
        for hotel in queryset:
            hotel.update_average_rating()
        self.message_user(request, _("Rating rata-rata hotel telah diperbarui."))
    update_average_rating.short_description = _("Perbarui rating rata-rata")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'multiple_images' in request.FILES:
            for image in request.FILES.getlist('multiple_images'):
                HotelGallery.objects.create(
                    hotel=obj,
                    image=image,
                    caption=f"Gambar untuk {obj.name}"
                )

# ====================
# HotelGallery Admin
# ====================
@admin.register(HotelGallery)
class HotelGalleryAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'caption', 'image']
    search_fields = ['hotel__name', 'caption']
    list_filter = ['hotel']

# ====================
# RoomType Admin
# ====================
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel', 'base_price']
    search_fields = ['name', 'hotel__name', 'description']
    list_filter = ['hotel']
    ordering = ['name']
    inlines = [RoomInline]

# ====================
# Facility Admin
# ====================
@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

# ====================
# Room Admin
# ====================
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'room_type', 'hotel', 'is_available']
    list_filter = ['room_type', 'hotel', 'is_available']
    search_fields = ['number', 'room_type__name', 'hotel__name']
    filter_horizontal = ['facilities']
    ordering = ['number']

# ====================
# Reservation Admin
# ====================
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'check_in', 'check_out', 'total_price', 'status', 'created_at']
    search_fields = ['user__username', 'room__number', 'room__hotel__name']
    list_filter = ['status', 'check_in', 'check_out', 'room__hotel']
    ordering = ['-created_at']
    inlines = [PaymentInline, ReviewInline]
    readonly_fields = ['created_at', 'total_price']
    actions = ['mark_as_checked_in', 'mark_as_checked_out', 'mark_as_cancelled']

    def mark_as_checked_in(self, request, queryset):
        updated = queryset.filter(status__in=['PENDING', 'PAID']).update(status='CHECKED_IN')
        self.message_user(request, f"{updated} reservasi telah ditandai sebagai Check-in.")
    mark_as_checked_in.short_description = _("Tandai sebagai Check-in")

    def mark_as_checked_out(self, request, queryset):
        updated = queryset.filter(status='CHECKED_IN').update(status='CHECKED_OUT')
        self.message_user(request, f"{updated} reservasi telah ditandai sebagai Check-out.")
    mark_as_checked_out.short_description = _("Tandai sebagai Check-out")

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=['PENDING', 'PAID']).update(status='CANCELLED')
        self.message_user(request, f"{updated} reservasi telah dibatalkan.")
    mark_as_cancelled.short_description = _("Batalkan reservasi")

# ====================
# Payment Admin
# ====================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'method', 'is_paid', 'paid_at']
    list_filter = ['is_paid', 'method', 'paid_at']
    search_fields = ['reservation__user__username', 'reservation__room__number', 'reservation__room__hotel__name']
    readonly_fields = ['paid_at']

# ====================
# Review Admin
# ====================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'rating', 'comment', 'created_at']
    search_fields = ['reservation__user__username', 'reservation__room__number', 'reservation__room__hotel__name', 'comment']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']