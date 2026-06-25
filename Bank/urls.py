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
    "buy_data_success/",
    views.buy_data_success,
    name="buy_data_success"
),

path('confirm_airtime/', views.confirm_airtime, name= "confirm_airtime"),
path('confirm-success/', views.airtime_success, name= "confirm_success"),
path('buy_airtime/', views.buy_airtime, name= "buy_airtime"),
path('airtime_success/', views.airtime_success, name= "airtime_success"),

path('confirm_electricity/', views.confirm_electricity, name= "confirm_electricity"),





]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)