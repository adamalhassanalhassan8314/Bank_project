from django.contrib import admin
from .models import Wallet, Profile, Transfer


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'fullname',
        'phone',
        'email',
        'pin'
    ]


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'balance'
    ]


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'account_name',
        'account_number',
        'amount',
        'status',
        'created_at'
    ]