from .contact import contact_details


def site_contact(request):
    contact = contact_details()
    return {'contact': contact, 'contact_email': contact['email']}


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
