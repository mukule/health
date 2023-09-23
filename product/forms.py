from django import forms
from .models import *

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control-lg'}),
    }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'price', 'image', 'category', 'quantity']  # Include 'quantity' field

    widgets = {
        'title': forms.TextInput(attrs={'class': 'form-control'}),
        'price': forms.NumberInput(attrs={'class': 'form-control'}),
        'image': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': 'image/*'}),
        'category': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),  # Add widget for 'quantity' field
    }

class StockTakeItemForm(forms.ModelForm):
    class Meta:
        model = StockTakeItem
        fields = ['product', 'quantity_counted']

    widgets = {
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity_counted': forms.NumberInput(attrs={'class': 'form-control'}),
    }

class StockTakeItemUpdateForm(forms.ModelForm):
    class Meta:
        model = StockTakeItem
        fields = ['quantity_counted']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity_counted'].widget.attrs.update({'class': 'form-control'})