from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import StudentRegistrationForm
from .tokens import email_verification_token
from .forms import CustomPasswordChangeForm

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            current_site = get_current_site(request)
            subject = 'Verify your email - Lab Portal'
            message = render_to_string('users/verify_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': email_verification_token.make_token(user),
            })
            send_mail(subject, message, 'noreply@labportal.com', [user.email])
            return HttpResponse('Check your email to verify your account.')
    else:
        form = StudentRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and email_verification_token.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.save()
        return HttpResponse('Email verified successfully! You can now log in.')
    else:
        return HttpResponse('Invalid or expired token.')   

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html', {'user': request.user})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            return render(request, 'users/change_password_done.html')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})