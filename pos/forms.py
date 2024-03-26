from product.models import *
from django import forms
from .models import *


class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(
        min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['receiver', 'cc']


class CashupForm(forms.ModelForm):
    class Meta:
        model = Cashup
        fields = ['total_sales', 'expenses', 'cash_at_hand']
        widgets = {
            'total_sales': forms.NumberInput(attrs={'class': 'form-control'}),
            'expenses': forms.NumberInput(attrs={'class': 'form-control'}),
            'cash_at_hand': forms.NumberInput(attrs={'class': 'form-control'}),
        }
