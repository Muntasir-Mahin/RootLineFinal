from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from dashboard.services import request_seller_access
from .forms import RegisterForm, ProfileUpdateForm
from .navigation import internal_next
from django.urls import reverse
from urllib.parse import urlencode


def home_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    return redirect('login')


def register_view(request):
    next_url = internal_next(request.POST.get('next') or request.GET.get('next'))
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account was created. You can now sign in.')
            if next_url:
                return redirect(reverse('login') + '?' + urlencode({'next':next_url}))
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'next_url':next_url})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            from partners.auth import authenticate_legacy_company
            user = authenticate_legacy_company(request, username, password)
        if user is not None:
            login(request, user)
            destination = internal_next(request.POST.get('next') or request.GET.get('next'))
            if destination:
                return redirect(destination)
            return redirect('profile')
        messages.error(request, 'The username or password was not recognised. Please try again.')
    return render(request, 'accounts/login.html', {'next_url':internal_next(request.POST.get('next') or request.GET.get('next'))})


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def become_seller_view(request):
    if request.method == 'POST':
        request_seller_access(request.user.pk)
        messages.success(request, 'Your seller request was sent for review.')
        return redirect('profile')
    return redirect('profile')


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def logout_view(request):
    if request.method == 'POST':
        if request.POST.get('confirm') != 'yes':
            return redirect('logout')
        if request.POST.get('user_id') != str(request.user.pk):
            messages.info(request, 'Your signed-in account changed. Please confirm logout again.')
            return redirect('logout')
        logout(request)
        return redirect('login')
    return render(request, 'accounts/logout.html')


@never_cache
@require_GET
def logout_token_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'signedOut': True})
    return JsonResponse({'csrfToken': get_token(request), 'userId': request.user.pk})


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was changed.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def seller_dashboard_view(request):
    if not request.user.seller_approved:
        return redirect('profile')
    return render(request, 'accounts/seller_dashboard.html')


@login_required
@require_POST
def toggle_theme_view(request):
    theme = request.POST.get('theme', 'light')
    if theme in ['light', 'dark']:
        request.user.theme_preference = theme
        request.user.save(update_fields=['theme_preference'])
        return JsonResponse({'status': 'success', 'theme': theme})
    return JsonResponse({'status': 'error'}, status=400)