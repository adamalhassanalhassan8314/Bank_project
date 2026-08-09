from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile,Transfer,Transaction
import random
from .models import Wallet
from django.conf import settings
import requests
from django.contrib import messages
from decimal import Decimal
from django.http import HttpResponse
from django.http import JsonResponse
import uuid
import json

# all this is for download pdf amma dole saikai ## pip install reportlab

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from django.contrib.auth import update_session_auth_hash




# public_key = settings.PAYSTACK_PUBLIC_KEY
# secret_key = settings.PAYSTACK_SECRET_KEY

# public_key = settings.FLUTTERWAVE_PUBLIC_KEY
# secret_key = settings.FLUTTERWAVE_SECRET_KEY
public_key = settings.FLUTTERWAVE_PUBLIC_KEY
secret_key = settings.FLUTTERWAVE_SECRET_KEY


settings.CLUBKONNECT_API_KEY



def page(request):
    return render(request, 'page.html')

def wellcome(request):
    return render(request, 'wellcome.html')

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        fullname = request.POST.get('fullname')

        if User.objects.filter(username=username).exists():
           return render(request, 'register.html', {'error': 'Username exists'})

        if Profile.objects.filter(phone=phone).exists():
           return render(request, 'register.html', {'error': 'Phone exists'})

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        profile = Profile.objects.get(user=user)
        profile.phone = phone
        profile.fullname = fullname
        profile.save()

        # OTP ka saka a session (MAFI SAUKI)
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['phone'] = phone

        print("OTP:", otp)

        return redirect('verify_otp')

    return render(request, 'register.html')



def user_login(request):

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'login.html') 


def logout_view(request):
    logout(request)
    return redirect("login")



def verify_otp(request):
    phone = request.session.get('phone')
    otp = request.session.get('otp')

    print("SESSION PHONE =", phone)
    print("SESSION OTP =", otp)

    if request.method == "POST":
        user_otp = request.POST.get('otp')

        print("USER OTP =", user_otp)

        if str(user_otp).strip() == str(otp).strip():
            return redirect('create_pin')
        else:
            return render(
                request,
                'verify_otp.html',
                {'error': 'Invalid OTP'}
            )

    return render(request, 'verify_otp.html')



@login_required(login_url='login')
def create_pin(request):

    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":

        pin = request.POST.get('pin')

        profile.pin = pin
        profile.save()

        return redirect('dashboard')

    return render(request, "create_pin.html")


@login_required(login_url='login')
def dashboard(request):

    profile = Profile.objects.get(user=request.user)

    wallet, created = Wallet.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        if request.FILES.get('image'):
            profile.image = request.FILES['image']
            profile.save()

    context = {
        'profile': profile,
        'wallet': wallet
    }

    return render(request, 'dashboard.html', context)    



        

def add_money(request):

    if request.method == "POST":

        amount = request.POST.get("amount")
        email = request.user.email

        url = "https://api.flutterwave.com/v3/payments"

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
    "tx_ref": str(uuid.uuid4()),
    "amount": amount,
    "currency": "NGN",
    "redirect_url": "http://127.0.0.1:8000/payment-success/",
    "customer": {
        "email": email,
        "name": request.user.username,
    },
    "customizations": {
        "title": "Wallet Funding"
    }
}

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(response.text)

        res = response.json()

        if res.get("status") == "success":
            payment_link = res["data"]["link"]
            return redirect(payment_link)

    return render(request, "add_money.html")



def payment_success(request):
    transaction_id = request.GET.get("transaction_id")

    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"

    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
    }

    response = requests.get(url, headers=headers)
    res = response.json()

    if (
        res.get("status") == "success"
        and res["data"]["status"] == "successful"
    ):

        amount = res["data"]["amount"]

        wallet = Wallet.objects.get(user=request.user)

        wallet.balance += amount
        wallet.save()

        return redirect("dashboard")

    return redirect("add_money")




@login_required
def buy_data(request):

    try:
        response = requests.get(
            "https://www.nellobytesystems.com/APIDatabundlePlansV2.asp?UserID=CK101279181"
        )

        data = response.json()

        networks = {}

        for network_name, network_data in data["MOBILE_NETWORK"].items():

            plans = network_data[0]["PRODUCT"]

            # ADD PROFIT
            for plan in plans:

                amount = float(
                    str(plan["PRODUCT_AMOUNT"]).replace(",", "")
                )

                if amount < 300:
                    profit = 50

                elif amount < 1000:
                    profit = 100

                else:
                    profit = 200

                plan["SELL_PRICE"] = amount + profit

            networks[network_name] = {
                "id": network_data[0]["ID"],
                "plans": plans
            }

    except Exception as e:

        print("API ERROR:", e)

        networks = {}

    if request.method == "POST":

        network = request.POST.get("network")
        phone = request.POST.get("phone")
        plan_id = request.POST.get("plan_id")
        plan_name = request.POST.get("plan_name")
        amount = request.POST.get("amount")

        request.session["network"] = network
        request.session["phone"] = phone
        request.session["plan_id"] = plan_id
        request.session["plan_name"] = plan_name
        request.session["amount"] = amount

        return redirect("confirm_data")

    context = {
        "networks": networks,
        "networks_json": json.dumps(networks)
    }

    return render(
        request,
        "buy_data.html",
        context
    )



@login_required
def confirm_data(request):

    network = request.session.get("network")
    phone = request.session.get("phone")
    plan_id = request.session.get("plan_id")
    plan_name = request.session.get("plan_name")

    amount = Decimal(
        request.session.get("amount", "0")
    )

    if request.method == "POST":

        pin = request.POST.get("pin")

        profile = Profile.objects.get(
            user=request.user
        )

        if profile.pin != pin:

            messages.error(
                request,
                "Incorrect PIN"
            )

            return redirect(
                "confirm_data"
            )

        wallet = Wallet.objects.get(
            user=request.user
        )

        if wallet.balance < amount:

            messages.error(
                request,
                "Insufficient Balance"
            )

            return redirect(
                "confirm_data"
            )

        # Convert 08123456789 => 2348123456789
        if phone and phone.startswith("0"):
            phone = "234" + phone[1:]

        network_map = {
            "MTN": "01",
            "GLO": "02",
            "9MOBILE": "03",
            "AIRTEL": "04",
        }

        network_id = network_map.get(network)

        params = {
            "UserID": "CK101279181",
            "APIKey": "98QM7PHX3WLE2U3ZQ40180KM1IIT4D5EM99Y04H1JRBB356EVB2CX2T38825G383",
            "MobileNetwork": network_id,
            "DataPlan": plan_id,
            "MobileNumber": phone,
            "RequestID": f"{request.user.id}-{phone}"
        }
             

        print("NETWORK =", network)
        print("NETWORK ID =", network_id)
        print("PLAN ID =", plan_id)
        print("PHONE =", repr(phone))
        print("PARAMS =", params)

        response = requests.get(
            "https://www.nellobytesystems.com/APIDatabundleV1.asp",
            params=params
        )

        print("URL =", response.url)
        print("TEXT =", response.text)

        data = response.json()

        if data.get("status") == "ORDER_RECEIVED":

            wallet.balance -= amount
            wallet.save()

            Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transactiontype="Data",
                    network=network,
                    receiver=phone,
                    reference=data.get("reference"),
                    status="Successful",
                )
            

            messages.success(
                request,
                "Data Purchase Successful"
            )

            return redirect(
                "buy_data_success"
            )

        else:

            messages.error(
                request,
                data.get(
                    "status",
                    "Transaction Failed"
                )
            )

            return redirect(
                "confirm_data"
            )

    context = {
        "network": network,
        "phone": phone,
        "amount": amount,
        "plan_name": plan_name,
    }

    return render(
        request,
        "confirm_data.html",
        context
    )



@login_required
def buy_data_success(request):

    return render(
        request,
        "buy_data_success.html"
    )



def get_plans(request):

    url = (
        "https://www.nellobytesystems.com/"
        "APIDatabundlePlansV2.asp"
        "?UserID=CK101279181"
    )

    response = requests.get(url)

    data = response.json()
    print(data,123456)

    return JsonResponse(data, safe=False)

def verify_account(request):

    if request.method == "POST":

        account_number = request.POST.get(
            "account_number"
        )

        bank_code = request.POST.get(
            "bank_code"
        )

        amount = request.POST.get(
            "amount"
        )

        url = (
            f"https://api.flutterwave.co/bank/resolve?"
            f"account_number={account_number}"
            f"&bank_code={bank_code}"
        )

        headers = {

            "Authorization":
            f"Bearer {settings.FULLTERWAVE_SECRET_KEY}"
        }

        response = requests.get(
            url,
            headers=headers
        )

        data = response.json()

        if data["status"]:

            request.session["account_number"] = (
                account_number
            )

            request.session["bank_code"] = (
                bank_code
            )

            request.session["amount"] = (
                amount
            )

            request.session["account_name"] = (
                data["data"]["account_name"]
            )

            return render(
                request,
                "confirm_transfer.html",
                {
                    "account_name":
                    data["data"]["account_name"],

                    "account_number":
                    account_number,

                    "amount":
                    amount
                }
            )

    return render(
        request,
        "transfer.html"
    )



@login_required
def transfer_money(request):

    account_number = request.session.get(
        "account_number"
    )

    bank_code = request.session.get(
        "bank_code"
    )

    amount = request.session.get(
        "amount"
    )

    account_name = request.session.get(
        "account_name"
    )

    # CHECK SESSION

    if not amount:

        request.session.flush()

        messages.error(
            request,
            "Session Expired"
        )

        return redirect("transfer")

    # CONVERT TO DECIMAL

    amount = Decimal(amount)

    # GET WALLET

    wallet = Wallet.objects.get(
        user=request.user
    )

    # CHECK BALANCE

    if wallet.balance < amount:

        messages.error(
            request,
            "Insufficient Balance"
        )

        return redirect("transfer")

    # HEADERS

    headers = {

        "Authorization":
        f"Bearer {settings.FULLTERWAVE_SECRET_KEY}",

        "Content-Type":
        "application/json"
    }

    # CREATE RECIPIENT

    recipient_url = (
        "https://api.flutterwave.co/transferrecipient"
    )

    recipient_data = {

        "type": "nuban",

        "name": account_name,

        "account_number": account_number,

        "bank_code": bank_code,

        "currency": "NGN"
    }

    recipient_response = requests.post(

        recipient_url,

        json=recipient_data,

        headers=headers
    )

    recipient_json = recipient_response.json()

    print(recipient_json)

    # CHECK RECIPIENT

    if not recipient_json["status"]:

        messages.error(
            request,
            "Recipient Creation Failed"
        )

        return redirect("transfer")

    recipient_code = (
        recipient_json["data"]["recipient_code"]
    )

    # TRANSFER

    transfer_url = (
        "https://api.flutterwave.co/transfer"
    )

    profile = Profile.objects.get(user=request.user)

    wallet, created = Wallet.objects.get_or_create(
        user=request.user
    )

    transfer_data = {

        "source": "balance",

        "amount": int(amount * 100),

        "recipient": recipient_code,

        "reason": "Wallet Transfer"
    }

    transfer_response = requests.post(

        transfer_url,

        json=transfer_data,

        headers=headers
    )

    transfer_json = transfer_response.json()

    print(transfer_json)

    # SUCCESS

    if transfer_json["status"]:

        wallet.balance -= amount

        wallet.save()

        Transfer.objects.create(

            user=request.user,

            account_name=account_name,

            account_number=account_number,

            amount=amount,

            status="Successful"
        )

        # SAVE SUCCESS DATA

        request.session["success_amount"] = str(amount)

        request.session["success_name"] = account_name

        # CLEAR OLD TRANSFER SESSION

        del request.session["account_number"]
        del request.session["bank_code"]
        del request.session["amount"]
        del request.session["account_name"]

        return redirect("transfer_success")

    # FAILED

    else:

        Transfer.objects.create(

            user=request.user,

            account_name=account_name,

            account_number=account_number,

            amount=amount,

            status="Failed"
        )

        messages.error(
            request,
            "Transfer Failed"
        )
    context = {
     "profile": profile,
     "wallet": wallet
    }
    return redirect("transfer", context)
    
@login_required
def enter_pin(request):

    return render(
        request,
        "enter_pin.html"
    )



@login_required
def put_pin(request):

    if request.method == "POST":

        pin = request.POST.get("pin")

        profile = Profile.objects.get(
            user=request.user
        )

        # CHECK PIN

        if profile.pin != pin:

            messages.error(
                request,
                "Incorrect PIN"
            )

            return redirect("put_pin")

        # GET DATA FROM SESSION

        phone = request.session.get("phone")
        network = request.session.get("network")
        plan = request.session.get("plan")

        # GET WALLET

        wallet = Wallet.objects.get(
            user=request.user
        )

        # CHECK BALANCE

        if wallet.balance < amount:

            messages.error(
                request,
                "Insufficient Balance"
            )

            return redirect("buy_data")

        # BUY DATA HERE

        # IF SUCCESS

        wallet.balance -= amount
        wallet.save()

        request.session.flush()

        return redirect(
            "data_success"
        )

    return render(
        request,
        "put_pin.html"
    )



def cable(request):
    return render(request, 'cable.html')
def international_airtime(request):
    return render(request, 'international.html')
def Edu_pin (request):
    return render(request, 'edu_pin.html')
def Bulk_sms(request):
    return render(request, "bulk_sms.html")
def referrals(request):
    return render(request, 'referral.html')
def airtime_swap(request):
    return render(request, 'airtime_swap')

def airtime_swap(request):
    return render(request, 'airtime_swap.html')

def top_up(request):
    return render(request, 'top_up.html')
def bonus(request):
    return render(request, "bonus.html")
def history(request):
    return render(request, "history.html")



@login_required
def transfer_success(request):

    return render(
        request,
        "transfer_success.html"
    )



@login_required
def airtime_success(request):

    transaction = Transaction.objects.filter(
        user=request.user,
        transactiontype="Airtime"
    ).order_by("-created_at").first()

    context = {
        "transaction": transaction
    }

    return render(
        request,
        "airtime_success.html",
        context
    )



def buy_airtime(request):
    if request.method == "POST":
        phone = request.POST.get('phone')

        request.session['phone'] = phone

        return redirect('airtime')
    return render(request, 'buy_airtime.html')


 
    


def buy_airtime(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        network = request.POST.get("network")

        request.session["phone"] = phone
        request.session["network"] = network

        return redirect("airtime")

    return render(request, "buy_airtime.html")




@login_required
def airtime(request):

    phone = request.session.get("phone")
    network = request.session.get("network")

    networks = {
        "01": "MTN",
        "02": "AIRTEL",
        "03": "GLO",
        "04": "9MOBILE"
    }
    wallet = Wallet.objects.get(user=request.user)
    network_name = networks.get(network, network)

    if request.method == "POST":

        amount = request.POST.get("amount")

        request.session["amount"] = amount

        return redirect("confirm_airtime")

    context = {
        "phone": phone,
        "network": network_name,
        "wallet": wallet
    }

    return render(
        request,
        "airtime.html",
        context
    )




@login_required
def confirm_airtime(request):

    phone = request.session.get("phone")
    amount = request.session.get("amount")
    network = request.session.get("network")

    networks = {
        "01": "MTN",
        "02": "AIRTEL",
        "03": "GLO",
        "04": "9MOBILE"
    }

    network_name = networks.get(network, network)

    if request.method == "POST":

        pin = request.POST.get("pin")

        profile = Profile.objects.get(
            user=request.user
        )

        if profile.pin != pin:

            messages.error(
                request,
                "Invalid PIN"
            )

            return redirect(
                "confirm_airtime"
            )

        wallet = Wallet.objects.get(
            user=request.user
        )

         
        amount_decimal = Decimal(amount)

        if wallet.balance < amount_decimal:

            messages.error(
                request,
                "Insufficient Balance"
            )

            return redirect(
                "confirm_airtime"
            )

        params = {
            "UserID": "CK101279181",
            "APIKey": "6ZX786W1JMIN2ENEA4GO5LG07K81B7P37GN20GMQA0R0VJ80261241T3X2RU2Q79",
            "MobileNetwork": network,
            "Amount": amount,
            "MobileNumber": phone,
        }

        response = requests.get(
            "https://www.nellobytesystems.com/APIAirtimeV1.asp",
            params=params
        )

        data = response.json()

        print(data)

        if data.get("status") == "ORDER_RECEIVED":

            wallet.balance -= amount_decimal
            wallet.save()

            Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transactiontype="Airtime",
                    network=network_name,
                    receiver=phone,
                    reference=data.get("reference"),
                    status="Successful",
                )

            messages.success(
                request,
                "Airtime Purchase Successful"
            )

            return redirect(
                "airtime_success"
            )

        else:

            messages.error(
                request,
                data.get(
                    "status",
                    "Purchase Failed"
                )
            )

            return redirect(
                "confirm_airtime"
            )

    context = {
        "phone": phone,
        "amount": amount,
        "network": network_name,
    }

    return render(
        request,
        "confirm_airtime.html",
        context
    )





@login_required
def cable(request):

    try:

        response = requests.get(
            "https://www.nellobytesystems.com/APICableTVPackagesV2.asp?UserID=CK101279181"
        )

        data = response.json()

        cables = {}

        for cable_name, cable_data in data.items():

            cables[cable_name] = {
                "plans": cable_data
            }

    except Exception as e:

        print("CABLE ERROR =", e)

        cables = {}

    if request.method == "POST":

        cabletv = request.POST.get("cabletv")
        smartcard = request.POST.get("smartcard")
        phone = request.POST.get("phone")
        package = request.POST.get("package")
        package_name = request.POST.get("package_name")
        amount = request.POST.get("amount")

        request.session["cabletv"] = cabletv
        request.session["smartcard"] = smartcard
        request.session["phone"] = phone
        request.session["package"] = package
        request.session["package_name"] = package_name
        request.session["amount"] = amount

        return redirect("confirm_cable")

    context = {

        "cables": cables,

        "cables_json": json.dumps(cables)

    }

    print(cables.keys())

    return render(
        request,
        "cable.html",
        context
    )


@login_required
def confirm_cable(request):

    cabletv = request.session.get("cabletv")
    smartcard = request.session.get("smartcard")
    phone = request.session.get("phone")
    package = request.session.get("package")
    package_name = request.session.get("package_name")

    amount = Decimal(
        request.session.get("amount", "0")
    )

    if request.method == "POST":

        pin = request.POST.get("pin")

        profile = Profile.objects.get(
            user=request.user
        )

        if profile.pin != pin:

            messages.error(
                request,
                "Invalid PIN"
            )

            return redirect(
                "confirm_cable"
            )

        wallet = Wallet.objects.get(
            user=request.user
        )

        if wallet.balance < amount:

            messages.error(
                request,
                "Insufficient Balance"
            )

            return redirect(
                "confirm_cable"
            )

        params = {

            "UserID": "CK101279181",

            "APIKey": "06H2YV0Y728QY4JAJJJB98FV3A15D0DCR134S19GE327F390G74P71WHI60I4NGJ",

            "CableTV": cabletv,

            "Package": package,

            "SmartCardNo": smartcard,

            "PhoneNo": phone,

            "RequestID": str(
                request.user.id
            )
        }

        response = requests.get(
            "https://www.nellobytesystems.com/APICableTVV1.asp",
            params=params
        )

        data = response.json()
        print(data)

        if data.get("status") == "ORDER_RECEIVED":

            wallet.balance -= amount

            wallet.save()

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transactiontype="Cable",
                network=cabletv,
                receiver=smartcard,
                reference=data.get("reference"),
                status="Successful",
               )
            messages.success(
                request,
                "Cable Subscription Successful"
            )

            return redirect(
                "dashboard"
            )

        else:

            messages.error(
                request,
                data.get(
                    "status",
                    "Transaction Failed"
                )
            )

            return redirect(
                "confirm_cable"
            )

    context = {

        "cabletv": cabletv,

        "smartcard": smartcard,

        "phone": phone,

        "package": package_name,

        "amount": amount

    }

    return render(
        request,
        "confirm_cable.html",
        context
    )






# def electricity(request):
#     if request.method=="POST":

#         company = request.POST.get('company')
#         meter_type = request.POST.get('meter_type')
#         meter_no = request.POST.get('meter_no')
#         phone = request.POST.get('phone')
#         amount = request.POST.get('amount')
#         customer_name = request.POST.get('custormer_name')




#         request.session["company"] = company
#         request.session["meter_type"] = meter_type
#         request.session["meter_no"] = meter_no
#         request.session["phone"] = phone
#         request.session["amount"] = amount
#         request.session["customer_name"] = customer_name
       

#         return redirect ('confirm_electricity')
    
#     return render(request, "electricity.html")






# @login_required
# def confirm_electricity(request):

#     company = request.session.get("company")
#     meter_type = request.session.get("meter_type")
#     meter_no = request.session.get("meter_no")
#     phone = request.session.get("phone")
#     amount = request.session.get("amount")
#     customer_name = request.session.get("customer_name")

#     if request.method == "POST":

#         pin = request.POST.get("pin")

#         profile = Profile.objects.get(
#             user=request.user
#         )

#         if profile.pin != pin:

#             messages.error(
#                 request,
#                 "INVALID PIN"
#             )

#             return redirect(
#                 "confirm_electricity"
#             )

#         wallet = Wallet.objects.get(
#             user=request.user
#         )

#         amount_decimal = Decimal(amount)

#         if wallet.balance < amount_decimal:

#             messages.error(
#                 request,
#                 "INSUFFICIENT BALANCE"
#             )

#             return redirect(
#                 "confirm_electricity"
#             )

#         url = "https://www.nellobytesystems.com/APIElectricityV1.asp"


#         profile = Profile.objects.get(
#              user=request.user
#          )
#         phone = profile.phone

#         params = {
#             "UserID": "CK101279181",
#             "APIKey": "08EOIW2O832323D6I47D7643W3HX0V3SERO2U9A5ZX1JKTQ4M5ST7VSN94L777E5",
#             "ElectricCompany": company,
#             "MeterType": meter_type,
#             "MeterNo": meter_no,
#             "Amount": amount,
#             "PhoneNo": phone,
#             "RequestID": f"{request.user.id}-{meter_no}"
#         }

#         response = requests.get(
#             url,
#             params=params
#         )

#         data = response.json()

#         print(data)

#         if data.get("status") == "ORDER_RECEIVED":

#             wallet.balance -= amount_decimal
#             wallet.save()

#             messages.success(
#                 request,
#                 "Electricity Bill Successful"
#             )

#             return redirect(
#                 "electricity_success"
#             )

#         messages.error(
#             request,
#             data.get(
#                 "status",
#                 "Transaction Failed"
#             )
#         )

#         return redirect(
#             "confirm_electricity"
#         )

#     context = {
#         "company": company,
#         "meter_type": meter_type,
#         "meter_no": meter_no,
#         "phone": phone,
#         "amount": amount,
#         "customer_name": customer_name,
#     }

#     return render(
#         request,
#         "confirm_electricity.html",
#         context
#     )




def verify_meter(request):

    company = request.GET.get("company")
    meter_type = request.GET.get("meter_type")
    meter_no = request.GET.get("meter_no")

    url = "https://www.nellobytesystems.com/APIVerifyElectricityV1.asp"

    params = {
        "UserID": "CK101279181",
        "APIKey": "YOUR_API_KEY",
        "ElectricCompany": company,
        "MeterType": meter_type,
        "MeterNo": meter_no,
    }

    response = requests.get(url, params=params)

    data = response.json()

    return JsonResponse(data)
    


def electricity(request):
    if request.method =="POST":
        company = request.POST.get('company')
        meter_type = request.POST.get('meter_type')
        meter_no = request.POST.get('meter_no')
        amount = request.POST.get('amount')
        


        request.session['company']= company
        request.session['meter_type'] = meter_type
        request.session['meter_no']= meter_no
        request.session['amount']= amount

        url = "https://www.nellobytesystems.com/APIVerifyElectricityV1.asp"

        params = {
        "UserID": "CK101279181",
        "APIKey": "YOUR_API_KEY",
        "ElectricCompany": company,
        "MeterType": meter_type,
        "MeterNo": meter_no,
        "amount": "amont"
        }

        response = requests.get(url, params=params)

        data = response.json()
        return JsonResponse(data)

        return redirect("confirn_electricy")
    return render(request, electricity.html)


def confirm_electricity(request):
    company = request.session.get('company')
    meter_type = request.session.get('meter_type')
    meter_no = request.session.get('meter_no')
    amount = request.session.get('amount')

    if request.method == "POST":
         pin = request.POST.get('pin')
         profile = Profile.objects.get(
            user=request.user
            )
         if profile.pin != pin:
             
             messages.error(
                 request, "INVALID PIN"
             )

             return redirect(
                 confirm_electricity
             )
         wallet = Wallet.objects.get(
             user= request.user
         )

         amount_decimal = Decimal(amount)

         if wallet.balance < amount_decimal:
             messages.error(
                 request, "INSUFFICIENT BALANCE"
             )

             return redirect('confirm_electricity')
         
         profile = Profile.objects.get(
             user= request.user
         )
         phone = request.t
         url =""
         params ={
             "UserID": "",
             "APIkey": "",
             "company": company,
             "meter_type": meter_type,
             "meter_no": meter_no,
             "amount": amount,
             
         }

         response = requests.get(url, params=params)
         data = response.json()
         return JsonResponse(data)
    
    context={
        "company": company,
        "meter_type": meter_type,
        "meter_no": meter_no,
        "amount": amount,
        "wallet": wallet,

    },

    return render(request, "confirm_electricity", context)


         


@login_required
def content(request):

    profile = request.user.profile
    wallet = request.user.wallet

    context = {
        "profile": profile,
        "wallet": wallet,
    }

    return render(request, "content.html", context)

# @login_required
# def change_photo(request):

#     profile = request.user.profile

#     if request.method == "POST":

#         if "image" in request.FILES:

#             profile.image = request.FILES["image"]

#             profile.save()

#             messages.success(
#                 request,
#                 "Profile photo updated successfully."
#             )

#             return redirect("content")

#     return render(request, "change_photo.html")


@login_required
def change_photo(request):

    profile = request.user.profile

    if request.method == "POST":

        if "image" in request.FILES:

            profile.image = request.FILES["image"]
            profile.save()

            messages.success(
                request,
                "Profile picture updated successfully."
            )

            return redirect("content")

    return render(request, "change_photo.html")


@login_required
def history(request):

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    context = {
        "transactions": transactions
    }

    return render(request, "history.html", context)

    from django.shortcuts import get_object_or_404

@login_required
def transaction_detail(request, id):

    transaction = get_object_or_404(
        Transaction,
        id=id,
        user=request.user
    )

    context = {
        "transaction": transaction
    }

    return render(
        request,
        "transaction_detail.html",
        context
    )



from django.shortcuts import get_object_or_404

@login_required
def transaction_detail(request, id):

    transaction = get_object_or_404(
        Transaction,
        id=id,
        user=request.user
    )

    context = {
        "transaction": transaction
    }

    return render(
        request,
        "transaction_detail.html",
        context,

    )



@login_required
def download_receipt(request, id):

    transaction = get_object_or_404(
        Transaction,
        id=id,
        user=request.user
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Receipt_{transaction.id}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>B2DATA TRANSACTION RECEIPT</b>", styles["Title"])
    )

    elements.append(
        Paragraph("<br/><br/>", styles["Normal"])
    )

    data = [

        ["Transaction Type", transaction.transactiontype],

        ["Amount", f"₦{transaction.amount}"],

        ["Network", transaction.network],

        ["Receiver", transaction.receiver],

        ["Reference", transaction.reference],

        ["Status", transaction.status],

        ["Date", transaction.created_at.strftime("%d %B %Y %I:%M %p")],

    ]

    table = Table(data, colWidths=[180, 250])

    table.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),1,colors.grey),

            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#ede9fe")),

            ("TEXTCOLOR",(0,0),(0,-1),colors.indigo),

            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),

            ("BOTTOMPADDING",(0,0),(-1,-1),10),

        ])

    )

    elements.append(table)

    doc.build(elements)

    return response




@login_required
def edit_profile(request):

    profile = request.user.profile

    if request.method == "POST":

        profile.fullname = request.POST.get("fullname")
        profile.phone = request.POST.get("phone")
        profile.email = request.POST.get("email")

        profile.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("content")

    context = {
        "profile": profile
    }

    return render(
        request,
        "edit_profile.html",
        context
    )


@login_required
def reset_pin(request):

    profile = request.user.profile

    if request.method == "POST":

        old_pin = request.POST.get("old_pin")
        new_pin = request.POST.get("new_pin")
        confirm_pin = request.POST.get("confirm_pin")

        if profile.pin != old_pin:

            messages.error(
                request,
                "Old PIN is incorrect."
            )

            return redirect("reset_pin")

        if new_pin != confirm_pin:

            messages.error(
                request,
                "New PIN and Confirm PIN do not match."
            )

            return redirect("reset_pin")

        profile.pin = new_pin
        profile.save()

        messages.success(
            request,
            "Transaction PIN changed successfully."
        )

        return redirect("content")

    return render(
        request,
        "reset_pin.html"
    )


@login_required
def change_password(request):

    if request.method == "POST":

        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        if not user.check_password(old_password):

            messages.error(
                request,
                "Current password is incorrect."
            )

            return redirect("change_password")

        if new_password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("change_password")

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(
            request,
            "Password changed successfully."
        )

        return redirect("content")

    return render(
        request,
        "change_password.html"
    )


@login_required
def contact_support(request):

    return render(
        request,
        "contact_support.html"
    )


@login_required
def help_center(request):

    return render(
        request,
        "help_center.html"
    )


@login_required
def about(request):

    return render(
        request,
        "about.html"
    )


@login_required
def privacy_policy(request):

    return render(
        request,
        "privacy_policy.html"
    )

@login_required
def terms_conditions(request):

    return render(
        request,
        "terms_conditions.html"
    )