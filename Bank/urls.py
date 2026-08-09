from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[

    path('', views.page, name= "page"),
    path('wellcome/', views.wellcome, name= "wellcome"),
    path('register/', views.register, name="register"),
    path('login/', views.user_login, name = "login" ),
    path('verify_otp/', views.verify_otp, name = "verify_otp"),
    path('create-pin/', views.create_pin, name = "create_pin"),
    path('dashboard/', views.dashboard, name = "dashboard"),
    path('add-money/', views.add_money, name = "add_money"),
    path('airtime/', views.airtime, name = "airtime"),
    path('cable/',  views.cable, name = "cable"),
    path('electricity/',  views.electricity, name = "electricity"),
    path('international/',  views.international_airtime, name = "international"),
    path('edu/',  views.Edu_pin, name = "edu_pin"),
    path('bulk-sms/', views.Bulk_sms, name='bulk_sms'),
    path('Referral/',  views.referrals, name = "Referral"),
    path(
    "transfer/",
    views.verify_account,
    name="transfer"
),

path('get-plans/', views.get_plans, name='get_plans'),

path(
    "transfer-money/",
    views.transfer_money,
    name="transfer_money"
),
    path('airtime-swap/',  views.airtime_swap, name = "airtime_swap"),
    
    path('top-up/', views.top_up, name = "top_up"),
    path(
    "transfer-success/",
    views.transfer_success,
    name="transfer_success"
),

path(
    "enter-pin/",
    views.enter_pin,
    name="enter_pin"
),
path("payment-success/", views.payment_success, name="payment_success"),

path(
    "buy-data/",
    views.buy_data,
    name="buy_data"
),

path(
    "confirm-data/",
    views.confirm_data,
    name="confirm_data"
),

path(
    "transaction/<int:id>/",
    views.transaction_detail,
    name="transaction_detail"
),

path(
    "receipt/<int:id>/",
    views.download_receipt,
    name="download_receipt"
),

path(
    "buy_data_success/",
    views.buy_data_success,
    name="buy_data_success"
),

path(
    "edit-profile/",
    views.edit_profile,
    name="edit_profile"
),

path(
    "reset-pin/",
    views.reset_pin,
    name="reset_pin"
),

path(
    "change-password/",
    views.change_password,
    name="change_password"
),

path(
    "privacy_policy/",
    views.privacy_policy,
    name="privacy_policy"
),

path('about-B2DATA/', views.about, name='about-B2DATA'),
path('terms_conditions/', views.terms_conditions, name='terms_conditions'),
path('contact-support/', views.contact_support, name='contact_support'),
path('help-center/', views.help_center, name='help_center'),
path('con/', views.logout_view, name='logout'),
path('logout/', views.logout_view, name='logout'),
path('confirm_airtime/', views.confirm_airtime, name= "confirm_airtime"),
path('confirm-success/', views.airtime_success, name= "confirm_success"),
path('buy_airtime/', views.buy_airtime, name= "buy_airtime"),
path('airtime_success/', views.airtime_success, name= "airtime_success"),

path('confirm_electricity/', views.confirm_electricity, name= "confirm_electricity"),
path('content/', views.content, name= "content"),
path('bonus/', views.bonus, name= "bonus"),
path('history/', views.history, name= "history"),
path('change-photo/', views.change_photo, name= "change_photo"),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

