"""Public help and search; only content already visible publicly is searchable."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from agro_updates.models import Video
from products.models import Product


@require_GET
def site_search(request):
    query = request.GET.get('q', '').strip()[:150]
    category = request.GET.get('category', '').strip()[:100]
    products = Product.objects.none()
    videos = Video.objects.none()
    if query or category:
        products = Product.objects.filter(
            verification_status='verified', is_available=True, stock_quantity__gt=0,
        )
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) |
                                       Q(category__icontains=query))
        if category:
            products = products.filter(category=category)
        products = products.order_by('-updated_at', '-pk')
    if query:
        videos = Video.objects.filter(
            is_published=True, published_at__lte=timezone.now(),
        ).filter(Q(title__icontains=query) | Q(summary__icontains=query) |
                 Q(channel_name__icontains=query)).order_by('-published_at', '-pk')
    return render(request, 'site/search.html', {
        'query': query,
        'search_category': category,
        'product_page': Paginator(products, 12).get_page(request.GET.get('products_page')),
        'video_page': Paginator(videos, 12).get_page(request.GET.get('videos_page')),
    })


@require_GET
def help_page(request):
    return render(request, 'site/help.html')
