from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import Notification


@never_cache
@login_required
@require_GET
def inbox(request):
    return render(request, 'notifications/inbox.html', {
        'page':Paginator(Notification.objects.filter(recipient=request.user), 25).get_page(request.GET.get('page'))})


@never_cache
@login_required
@require_POST
def mark_read(request, pk):
    item = get_object_or_404(Notification, pk=pk, recipient=request.user)
    Notification.objects.filter(pk=item.pk, recipient=request.user).update(is_read=True)
    return redirect('notifications:inbox')
