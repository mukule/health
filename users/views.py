from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login
from .forms import *
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .decorators import user_not_authenticated
from django.contrib.auth import authenticate, login
from .decorators import *
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from .forms import SetPasswordForm
from .forms import PasswordResetForm
from django.db.models.query_utils import Q
from django.contrib.auth.decorators import user_passes_test
import random
import string
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from users.forms import *


def is_admin_or_superuser(user):
    return user.is_superuser or (user.access_level == 1)


def not_authorized(request):
    return render(
        request,
        template_name="admin/not_authorized.html"
    )


@login_required
@user_passes_test(is_admin_or_superuser, login_url='users:not_authorized')
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            user.is_active = True
            user.save()
            return redirect('users:staffs')

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = UserRegistrationForm()

    return render(
        request=request,
        template_name="users/register.html",
        context={"form": form}
    )


@login_required
@user_passes_test(is_admin_or_superuser, login_url='users:not_authorized')
def update_user(request, user_id):
    # Retrieve the user instance
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        # Create a form instance and populate it with the current user's data
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User details updated successfully.')
            return redirect('users:staffs')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        # Create a form instance and populate it with the current user's data
        form = UserUpdateForm(instance=user)

    return render(
        request=request,
        template_name="users/update_staff.html",
        context={"form": form, "user": user}
    )


def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('users/template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Dear <b>{user}</b>, please go to you email <b>{to_email}</b> inbox and click on \
            received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
    else:
        messages.error(
            request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(
            request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('users:login')
    else:
        messages.error(request, 'Activation link is invalid!')

    return redirect('/')


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


@user_not_authenticated
def custom_login(request):
    if request.method == "POST":
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                messages.success(
                    request, f"Hello <b>{user.username}</b>! You have been logged in")
                return redirect("/")

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    form = UserLoginForm()

    return render(
        request=request,
        template_name="users/login.html",
        context={"form": form}
    )


def profile(request, username):
    if request.method == 'POST':
        user = request.user
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            print("Form is valid")

            user_form = form.save()
            print("User form saved:", user_form)

            messages.success(
                request, f'{user_form}, Your profile has been updated!')
            return redirect('users:profile', user_form.username)

        for error in list(form.errors.values()):
            messages.error(request, error)

    user = get_user_model().objects.filter(username=username).first()
    if user:
        form = UserUpdateForm(instance=user)
        print("User instance:", user)
        return render(request, 'users/profile.html', context={'form': form})

    return redirect("/")


@login_required
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed")
            return redirect('users:login')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    form = SetPasswordForm(user)
    return render(request, 'users/password_reset_confirm.html', {'form': form})


@user_not_authenticated
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset request"
                message = render_to_string("users/template_reset_password.html", {
                    'user': associated_user,
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    "protocol": 'https' if request.is_secure() else 'http'
                })
                email = EmailMessage(subject, message, to=[
                                     associated_user.email])
                if email.send():
                    messages.success(request,
                                     """
                        <h2>Password reset sent</h2><hr>
                        <p>
                            We've emailed you instructions for setting your password, if an account exists with the email you entered. 
                            You should receive them shortly.<br>If you don't receive an email, please make sure you've entered the address 
                            you registered with, and check your spam folder.
                        </p>
                        """
                                     )
                else:
                    messages.error(
                        request, "Problem sending reset password email, <b>SERVER PROBLEM</b>")

            return redirect('/')

    form = PasswordResetForm()
    return render(
        request=request,
        template_name="users/password_reset.html",
        context={"form": form}
    )


def passwordResetConfirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Your password has been set. You may go ahead and <b>log in </b> now.")
                return redirect('/')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)

        form = SetPasswordForm(user)
        return render(request, 'users/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "Link is expired")

    messages.error(
        request, 'Something went wrong, redirecting back to Homepage')
    return redirect("/")


@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("/")


@login_required
@user_passes_test(is_admin_or_superuser, login_url='users:not_authorized')
def staffs(request):
    staffs = CustomUser.objects.all()
    return render(request, 'users/staffs.html', {'staffs': staffs})


@login_required
@user_passes_test(is_admin_or_superuser, login_url='users:not_authorized')
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    user.delete()
    return redirect('users:staffs')


def not_allowed(request):
    return redirect(request, 'users/not_allowed.html')
