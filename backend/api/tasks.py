from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_verification_email(user_email, verification_code):
    subject = "Your Verification Code"
    message = f"Your verification code is: {verification_code}"
    from_email = "from@example.com"
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
