from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Wallet, Profile

@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        Profile.objects.create(user=instance, fullname="", phone="", email="")