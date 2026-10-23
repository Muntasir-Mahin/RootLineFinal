from django.urls import reverse

from notifications.services import create_notification


def seller_order_link(order):
    return reverse('seller_orders') + f'#seller-order-{order.pk}'


def order_placed(order):
    names = list(order.items.values_list('product_name', flat=True)[:4])
    products = ', '.join(names[:3]) + (' and more' if len(names) > 3 else '')
    create_notification(order.seller,
        f'New order #{order.pk}: {products}. Total BDT {order.total_amount:.2f}. Payment is not verified yet.',
        seller_order_link(order))


def payment_verified(order, payment):
    create_notification(order.seller,
        f'Payment verified for order #{order.pk}: BDT {payment.amount:.2f}. '
        'The payment is recorded as held in escrow; it has not been released to you yet.',
        seller_order_link(order))


def sale_completed(order, payment):
    create_notification(order.seller,
        f'Sale completed for order #{order.pk}. Escrow is recorded as released. '
        f'Seller amount BDT {payment.seller_amount:.2f}; commission BDT {payment.commission_amount:.2f}.',
        seller_order_link(order))
