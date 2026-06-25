from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    pin = models.CharField(max_length=10, null=True, blank=True)
    image = models.ImageField(upload_to='profiles/', default='default.png')

class Transfer(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    account_name = models.CharField(max_length=200)

    account_number = models.CharField(max_length=20)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transactiontype =models.CharField(max_length=50)
    sender = models.CharField(max_length=100, blank=True, null=True )
    reciever =models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default="Pending")
    # create_at = models.CharField(auto_now_add=True)

