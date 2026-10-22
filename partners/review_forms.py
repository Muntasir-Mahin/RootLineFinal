from django import forms


class CompanyReviewForm(forms.Form):
    rating = forms.TypedChoiceField(coerce=int, choices=[(value, f'{value} / 5') for value in range(5, 0, -1)])
    title = forms.CharField(max_length=160)
    comment = forms.CharField(max_length=4000, widget=forms.Textarea(attrs={'rows':5}))


class ReviewReplyForm(forms.Form):
    reply = forms.CharField(max_length=3000, widget=forms.Textarea(attrs={'rows':4}))


class ReviewReportForm(forms.Form):
    reason = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'rows':4}))
