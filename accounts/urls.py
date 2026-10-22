from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from .recovery_views import RecoveryPasswordResetView, UsernameRecoveryView
from .views import (
    register_view,
    login_view,
    profile_view,
    logout_view,
    logout_token_view,
    edit_profile_view,
    change_password_view,
    become_seller_view,
    seller_dashboard_view,
    home_view,
    toggle_theme_view,
)
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('password/reset/', RecoveryPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('username/recover/', UsernameRecoveryView.as_view(), name='username_recovery'),
    path('username/recover/sent/', TemplateView.as_view(
        template_name='accounts/username_recovery_done.html'), name='username_recovery_done'),
    path('logout/', logout_view, name='logout'),
    path('logout/token/', logout_token_view, name='logout_token'),

    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('password/change/', change_password_view, name='change_password'),

    path('become-seller/', become_seller_view, name='become_seller'),
    path('seller/dashboard/', seller_dashboard_view, name='seller_dashboard'),

    # Theme toggle route
    path('toggle-theme/', toggle_theme_view, name='toggle_theme'),
]

# Serve media files during development for profile pictures
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)