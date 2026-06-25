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


def user_logout(request):
    logout(request)
    return redirect ('login')



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

# @login_required
# def confirm_data(request):

#     network = request.session.get("network")
#     phone = request.session.get("phone")
#     plan_id = request.session.get("plan_id")
#     plan_name = request.session.get('plan_name')
    
#     amount = Decimal(
#     request.session.get("amount", "0")
# )
    
#     if request.method == "POST":

#         pin = request.POST.get("pin")

#         profile = Profile.objects.get(
#             user=request.user
#         )

#         if profile.pin != pin:

#             messages.error(
#                 request,
#                 "Incorrect PIN"
#             )

#             print("AMOUNT FROM FORM =", amount)

#             return redirect("confirm_data")

#         wallet = Wallet.objects.get(
#             user=request.user
#         )

#         if wallet.balance < amount:

#             messages.error(
#                 request,
#                 "Insufficient Balance"
#             )

#             return redirect("confirm_data")

#         url = (
#             "https://www.nellobytesystems.com/APIDatabundleV1.asp"
#         )
#         network_map = {
#             "MTN": "01",
#             "GLO": "02",
#             "9MOBILE": "03",
#             "AIRTEL": "04",
#         }

#         network_id = network_map.get(network)

#         params = {

#             "UserID": "CK101279181",

#             "APIKey": "147F000GH4393J5U15J9R6XAJI1WXC27276T73SS8K655PUQMZ4KV8P53OIRBB6Z",

#             "MobileNetwork": network_id,

#             "DataPlan": plan_id,

#             "MobileNumber": phone,

#             "RequestID": str(
#                 request.user.id
#             )
#         }

#         response = requests.get(
#             url,
#             params=params
#         )

#         data = response.json()

#         print(data)

#         if data.get("status") == "ORDER_RECEIVED":

#             wallet.balance -= Decimal(amount)

#             wallet.save()

#             return redirect(
#                 "buy_data_success"
#             )

#         else:

#             messages.error(
#                 request,
#                 data.get(
#                     "status",
#                     "Transaction Failed"
#                 )
#             )
#             print("NETWORK =", network)
#             print("PLAN ID =", plan_id)
#             print("PLAN NAME =", plan_name)
#             print("AMOUNT =", amount)

#             return redirect(
#                 "confirm_data"
#             )

#     context = {

#         "network": network,

#         "phone": phone,

#         "plan": plan_id,

#         "amount": amount,

#         "plan_name": plan_name
#     }

#     return render(
#         request,
#         "confirm_data.html",
#         context
#     )


    # network = request.session.get("network")
    # phone = request.session.get("phone")
    # plan_id = request.session.get("plan_id")
    # plan_name = request.session.get("plan_name")

    # amount = Decimal(
    #     request.session.get("amount", "0")
    # )

    # if request.method == "POST":

    #     pin = request.POST.get("pin")

    #     profile = Profile.objects.get(
    #         user=request.user
    #     )

    #     if profile.pin != pin:
    #         messages.error(
    #             request,
    #             "Incorrect PIN"
    #         )
    #         return redirect("confirm_data")

    #     wallet = Wallet.objects.get(
    #         user=request.user
    #     )

    #     if wallet.balance < amount:
    #         messages.error(
    #             request,
    #             "Insufficient Balance"
    #         )
    #         return redirect("confirm_data")

    #     network_map = {
    #         "MTN": "01",
    #         "GLO": "02",
    #         "9MOBILE": "03",
    #         "AIRTEL": "04",
    #     }

    #     network_id = network_map.get(network)

    #     print("NETWORK =", network)
    #     print("NETWORK ID =", network_id)
    #     print("PLAN ID =", plan_id)
    #     print("PHONE =", phone)
    #     print("AMOUNT =", amount)
        

    #     url = "https://www.nellobytesystems.com/APIDatabundleV1.asp"

    #     params = {
    #         "UserID": "YOUR_USER_ID",
    #         "APIKey": "YOUR_API_KEY",
    #         "MobileNetwork": network_id,
    #         "DataPlan": plan_id,
    #         "MobileNumber": phone,
    #         "RequestID": f"{request.user.id}-{phone}"
    #     }

    #     response = requests.get(
    #         url,
    #         params=params,
    #         timeout=30
    #     )

    #     print("URL =", response.url)
    #     print("TEXT =", response.text)

        # data = response.json()

    #     if data.get("status") == "ORDER_RECEIVED":

    #         wallet.balance -= amount
    #         wallet.save()

    #         return redirect(
    #             "buy_data_success"
    #         )

    #     messages.error(
    #         request,
    #         data.get(
    #             "status",
    #             "Transaction Failed"
    #         )
    #     )

    #     return redirect(
    #         "confirm_data"
    #     )

    # context = {
    #     "network": network,
    #     "phone": phone,
    #     "plan": plan_id,
    #     "amount": amount,
    #     "plan_name": plan_name,
    # }

    # return render(
    #     request,
    #     "confirm_data.html",
    #     context
    # )


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
            "APIKey": "A3O16I4GBW1Z6767JJ8K29L4U9R4Q320801GOQZV0LJ7DQ4FWQ8A475V0WE0BM34",
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

        return redirect("transfer")
    
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
def electricity(request):
    return render(request, 'electricity.html')
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


@login_required
def transfer_success(request):

    return render(
        request,
        "transfer_success.html"
    )


def airtime_success(request):
    return render(
        request,
        "airtime_success.html"
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





# def airtime(request):

#     phone = request.session.get("phone")
#     network = request.session.get("network")

#     if request.method == "POST":

#         amount = request.POST.get("amount")
       

#         request.session["amount"] = amount
        
#         return redirect("confirm_airtime")

#     context = {
#         "phone": phone,
#         "network": network
#     }

#     return render(request, "airtime.html", context)

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

    network_name = networks.get(network, network)

    if request.method == "POST":

        amount = request.POST.get("amount")

        request.session["amount"] = amount

        return redirect("confirm_airtime")

    context = {
        "phone": phone,
        "network": network_name,
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
            "APIKey": "3YI15VLJ1Y2OS32P5026P6YX561271FO3BA02E9WBK8UITNL39Q36K3U6CAT10I3",
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



from decimal import Decimal
from django.contrib import messages


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


# def create_transaction(request):
#     Transaction.objests.create(
#         user = request.user,
#         amount=amount,
#         transactiontype="Transfer",
#         sender = request.user.username,
#         reciever = account_name,
#         bank_name = bank_name,
#         account_number = account_number,
#         reference = reference,
#         description = "Bank Transfer"
#         Status = "Success"

#     )


# def create_transaction(request):
#     Transaction.objects.create(
#     user=request.user,
#     amount=amount,
#     transactiontype="Transfer",
#     sender=request.user.username,
#     reciever=account_name,
#     account_number=account_number,
#     reference=reference,
# )




def electricity(request):
    if request.method=="POST":

        company = request.POST.get('company')
        meter_type = request.POST.get('meter_type')
        meter_no = request.POST.get('meter_no')
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        customer_name = request.POST.get('custormer_name')




        request.session["company"] = company
        request.session["meter_type"] = meter_type
        request.session["meter_no"] = meter_no
        request.session["phone"] = phone
        request.session["amount"] = amount
        request.session["customer_name"] = customer_name
       

        return redirect ('confirm_electricity')
    
    return render(request, "electricity.html")






@login_required
def confirm_electricity(request):

    company = request.session.get("company")
    meter_type = request.session.get("meter_type")
    meter_no = request.session.get("meter_no")
    phone = request.session.get("phone")
    amount = request.session.get("amount")
    customer_name = request.session.get("customer_name")

    if request.method == "POST":

        pin = request.POST.get("pin")

        profile = Profile.objects.get(
            user=request.user
        )

        if profile.pin != pin:

            messages.error(
                request,
                "INVALID PIN"
            )

            return redirect(
                "confirm_electricity"
            )

        wallet = Wallet.objects.get(
            user=request.user
        )

        amount_decimal = Decimal(amount)

        if wallet.balance < amount_decimal:

            messages.error(
                request,
                "INSUFFICIENT BALANCE"
            )

            return redirect(
                "confirm_electricity"
            )

        url = "https://www.nellobytesystems.com/APIElectricityV1.asp"


        profile = Profile.objects.get(
             user=request.user
         )
        phone = profile.phone

        params = {
            "UserID": "CK101279181",
            "APIKey": "08EOIW2O832323D6I47D7643W3HX0V3SERO2U9A5ZX1JKTQ4M5ST7VSN94L777E5",
            "ElectricCompany": company,
            "MeterType": meter_type,
            "MeterNo": meter_no,
            "Amount": amount,
            "PhoneNo": phone,
            "RequestID": f"{request.user.id}-{meter_no}"
        }

        response = requests.get(
            url,
            params=params
        )

        data = response.json()

        print(data)

        if data.get("status") == "ORDER_RECEIVED":

            wallet.balance -= amount_decimal
            wallet.save()

            messages.success(
                request,
                "Electricity Bill Successful"
            )

            return redirect(
                "electricity_success"
            )

        messages.error(
            request,
            data.get(
                "status",
                "Transaction Failed"
            )
        )

        return redirect(
            "confirm_electricity"
        )

    context = {
        "company": company,
        "meter_type": meter_type,
        "meter_no": meter_no,
        "phone": phone,
        "amount": amount,
        "customer_name": customer_name,
    }

    return render(
        request,
        "confirm_electricity.html",
        context
    )

