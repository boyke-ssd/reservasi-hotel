from django.contrib import admin
from .models import (
    UserProfile, RoomType, Facility, Room,
    Reservation, Payment, Review
)

# ====================
# UserProfile Admin
# ====================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'gender']
    search_fields = ['user__username', 'phone']
    list_filter = ['gender']


# ====================
# RoomType Admin
# ====================
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price']
    search_fields = ['name']
    ordering = ['name']


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
    list_display = ['number', 'room_type', 'is_available']
    list_filter = ['room_type', 'is_available']
    search_fields = ['number']
    filter_horizontal = ['facilities']
    ordering = ['number']


# ====================
# Inline untuk Pembayaran
# ====================
class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ['paid_at']
    can_delete = False


# ====================
# Inline untuk Review
# ====================
class ReviewInline(admin.StackedInline):
    model = Review
    extra = 0
    readonly_fields = ['created_at']
    can_delete = False


# ====================
# Reservation Admin
# ====================
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'check_in', 'check_out', 'total_price', 'created_at']
    search_fields = ['user__username', 'room__number']
    list_filter = ['check_in', 'check_out']
    ordering = ['-created_at']
    inlines = [PaymentInline, ReviewInline]


# ====================
# Payment Admin
# ====================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'method', 'is_paid', 'paid_at']
    list_filter = ['is_paid', 'method']
    search_fields = ['reservation__user__username']
    readonly_fields = ['paid_at']


# ====================
# Review Admin
# ====================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'rating', 'created_at']
    search_fields = ['reservation__user__username', 'reservation__room__number']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']
