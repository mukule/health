from django import forms


class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
