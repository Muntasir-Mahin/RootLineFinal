from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import Certification, CompanyProduct, CompanyProfile, PartnerCategory


def page_context(request, queryset, *, size=12):
    return Paginator(queryset, size).get_page(request.GET.get('page'))


@require_GET
def directory(request):
    companies = CompanyProfile.objects.public().select_related('user').annotate(
        product_count=Count('products', filter=Q(products__is_active=True), distinct=True),
        average_rating=Avg('company_reviews__rating', filter=Q(company_reviews__is_visible=True)),
        review_count=Count('company_reviews', filter=Q(company_reviews__is_visible=True), distinct=True))
    query = request.GET.get('q', '').strip()[:150]
    district = request.GET.get('district', '').strip()[:100]
    category = request.GET.get('category', '').strip()[:100]
    if query:
        companies = companies.filter(name__icontains=query)
    if district:
        companies = companies.filter(district__iexact=district)
    if category:
        companies = companies.filter(Q(categories__slug=category) | Q(products__category__slug=category,
                                                                           products__is_active=True)).distinct()
    districts = CompanyProfile.objects.public().order_by('district').values_list('district', flat=True).distinct()
    return render(request, 'partners/directory.html', {'page': page_context(request, companies.order_by('name')),
        'query': query, 'district': district, 'category': category, 'districts': districts,
        'categories': PartnerCategory.objects.all()})


@require_GET
def store(request, slug):
    company = get_object_or_404(CompanyProfile.objects.public().select_related('user').prefetch_related(
        'achievements', 'certifications', 'gallery', 'categories'), slug=slug)
    products = company.products.filter(is_active=True).select_related('category', 'company')
    query = request.GET.get('q', '').strip()[:150]
    category = request.GET.get('category', '').strip()[:100]
    sort = request.GET.get('sort', 'newest')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category__slug=category)
    products = products.annotate(effective_price=Coalesce('discount_price', 'price'))
    products = products.order_by({'price_low': 'effective_price', 'price_high': '-effective_price'}.get(sort, '-created_at'), '-pk')
    reviews = company.company_reviews.filter(is_visible=True)
    ratings = reviews.aggregate(average=Avg('rating'), count=Count('pk'))
    counts = dict(reviews.order_by().values('rating').annotate(total=Count('pk')).values_list('rating', 'total'))
    return render(request, 'partners/store.html', {'company': company, 'page': page_context(request, products),
        'query': query, 'category': category, 'sort': sort,
        'ratings':ratings, 'rating_breakdown':[(value, counts.get(value, 0)) for value in range(5, 0, -1)],
        'review_page':Paginator(reviews, 6).get_page(request.GET.get('reviews_page')),
        'categories': PartnerCategory.objects.filter(products__company=company, products__is_active=True).distinct()})


@require_GET
def product_detail(request, slug, product_slug):
    company = get_object_or_404(CompanyProfile.objects.public(), slug=slug)
    product = get_object_or_404(CompanyProduct.objects.select_related('category', 'company').prefetch_related('extra_images'),
                              company=company, slug=product_slug, is_active=True)
    return render(request, 'partners/product_detail.html', {'company': company, 'product': product})


@require_GET
def certificate_download(request, slug, pk):
    company = get_object_or_404(CompanyProfile.objects.public(), slug=slug)
    certificate = get_object_or_404(Certification, pk=pk, company=company)
    if not certificate.file:
        from django.http import Http404
        raise Http404
    response = FileResponse(certificate.file.open('rb'), as_attachment=True)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "sandbox"
    return response
