from django.conf import settings


def site_contact(request):
    return {'contact_email': settings.ROOTLINE_CONTACT_EMAIL}


def marketplace_navigation(request):
    """Read-only public categories and the signed-in user's cart line count."""
    from django.db.models import Count
    from orders.models import CartItem
    from products.models import Product

    categories = Product.objects.filter(
        verification_status='verified', is_available=True, stock_quantity__gt=0,
    ).exclude(category='').values('category').annotate(count=Count('pk')).order_by('-count', 'category')
    return {
        'navigation_categories': list(categories),
        'navigation_cart_count': CartItem.objects.filter(cart__user=request.user).count()
        if request.user.is_authenticated else 0,
    }
