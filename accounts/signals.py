"""Signals responsible for sending activation e-mails whenever a new user
is created (either a tenant admin during sign up, or an employee created by
a tenant admin).
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import account_activation_token

User = get_user_model()


def build_activation_link(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    path = reverse('accounts:activate', kwargs={'uidb64': uidb64, 'token': token})
    domain = request.get_host() if request else 'localhost:8000'
    scheme = 'https' if request and request.is_secure() else 'http'
    return f'{scheme}://{domain}{path}'


def send_activation_email(user, activation_link):
    subject = 'Ative sua conta no SaaS Vendedor'
    message = render_to_string('accounts/email/activation_email.txt', {
        'user': user,
        'activation_link': activation_link,
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@receiver(post_save, sender=User)
def send_activation_email_on_creation(sender, instance, created, **kwargs):
    """Kept intentionally inert by default: the activation e-mail requires a
    request-built link with host information, so views trigger it explicitly
    via `send_activation_email`. This signal only exists as an extension
    point (e.g. for logging or auditing new accounts) and is safe to leave
    connected without side effects.
    """
    return
