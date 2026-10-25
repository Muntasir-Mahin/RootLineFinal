import logging
from hashlib import sha256

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView

from .recovery_forms import UsernameRecoveryForm


logger = logging.getLogger(__name__)


def recovery_attempt_allowed(scope, value, limit):
    # Hash addresses instead of retaining them in cache keys. Limits are shared
    # by both recovery endpoints and expire ten minutes after the first attempt.
    digest = sha256(value.encode('utf-8')).hexdigest()
    key = f'accounts:recovery:{scope}:{digest}'
    if cache.add(key, 1, timeout=600):
        return True
    try:
        return cache.incr(key) <= limit
    except ValueError:
        # The key may expire between add() and incr(). Fail closed if another
        # request has already recreated it.
        return cache.add(key, 1, timeout=600)


class RecoveryRateLimitMixin:
    def recovery_is_allowed(self, form):
        # REMOTE_ADDR comes from the server; do not trust client-supplied XFF.
        if not recovery_attempt_allowed('ip', self.request.META.get('REMOTE_ADDR', ''), 10):
            return False
        return recovery_attempt_allowed('email', form.cleaned_data['email'].casefold(), 3)


@method_decorator(never_cache, name='dispatch')
class RecoveryPasswordResetView(RecoveryRateLimitMixin, PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.txt'
    subject_template_name = 'accounts/password_reset_subject.txt'

    def form_valid(self, form):
        if not self.recovery_is_allowed(form):
            return redirect(self.get_success_url())
        return super().form_valid(form)


@method_decorator(never_cache, name='dispatch')
class UsernameRecoveryView(RecoveryRateLimitMixin, FormView):
    template_name = 'accounts/username_recovery_form.html'
    form_class = UsernameRecoveryForm
    success_url = reverse_lazy('username_recovery_done')

    def form_valid(self, form):
        if self.recovery_is_allowed(form):
            self.send_recovery_email(form)
        return super().form_valid(form)

    def send_recovery_email(self, form):
        User = get_user_model()
        email_field = User.get_email_field_name()
        users = list(User._default_manager.filter(
            **{f'{email_field}__iexact': form.cleaned_data['email'], 'is_active': True}
        ).order_by(User.USERNAME_FIELD).values_list(User.USERNAME_FIELD, email_field))
        if users:
            body = render_to_string('accounts/username_recovery_email.txt', {
                'usernames': [username for username, email in users],
                'login_url': self.request.build_absolute_uri(reverse_lazy('login')),
            })
            try:
                EmailMessage(
                    subject='Your RootLine username(s)',
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[users[0][1]],
                ).send()
            except Exception:
                # Delivery errors must not turn a known address into a different
                # public response. Operators can investigate the server log.
                logger.exception('Username recovery email could not be sent.')
