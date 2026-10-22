from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .models import CompanyProfile, CompanyReview, OrderRequest
from .review_forms import CompanyReviewForm, ReviewReplyForm, ReviewReportForm
from .review_services import create_review, reply_to_review, report_review
from .views import company_required


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def review_create(request, pk):
    order = get_object_or_404(OrderRequest, pk=pk, buyer=request.user, status='completed')
    if CompanyReview.objects.filter(order=order).exists():
        messages.info(request, 'This completed order already has a review.')
        return redirect('partners:buyer_order', pk=pk)
    form = CompanyReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            create_review(order.pk, buyer=request.user, data=form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, '; '.join(error.messages))
        else:
            messages.success(request, 'Your verified purchase review has been published.')
            return redirect('partners:buyer_order', pk=pk)
    return render(request, 'partners/form.html', {'form':form, 'title':f'Review {order.company.name}',
        'submit_label':'Publish review', 'intro':'One review per completed order. Reviews and company replies are public.'})


@company_required
@require_GET
def company_reviews(request):
    return render(request, 'partners/company_reviews.html', {'company':request.partner_company,
        'reviews':request.partner_company.company_reviews.select_related('order')})


@company_required
@require_http_methods(['GET', 'POST'])
def review_reply(request, pk):
    review = get_object_or_404(CompanyReview, pk=pk, company=request.partner_company)
    form = ReviewReplyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            reply_to_review(review.pk, actor=request.user, reply=form.cleaned_data['reply'])
        except ValidationError as error:
            form.add_error(None, '; '.join(error.messages))
        else:
            messages.success(request, 'Your public reply has been posted.')
            return redirect('partners:company_reviews')
    return render(request, 'partners/form.html', {'company':request.partner_company, 'form':form,
        'title':f'Reply to: {review.title}', 'submit_label':'Post public reply', 'intro':'You can post one public reply to this review.'})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def review_report(request, pk):
    review = get_object_or_404(CompanyReview, pk=pk, is_visible=True,
                              company__in=CompanyProfile.objects.public())
    form = ReviewReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        report_review(review.pk, reporter=request.user, reason=form.cleaned_data['reason'])
        messages.success(request, 'Your report has been sent to the owner for review.')
        return redirect(review.company.get_absolute_url() + '#partner-reviews')
    return render(request, 'partners/form.html', {'form':form, 'title':'Report a company review',
        'submit_label':'Send report', 'intro':'Explain why this review needs owner attention. Reporting does not automatically hide a review.'})
