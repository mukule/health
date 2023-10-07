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
    units = forms.CharField(
        max_length=50,
        required=False,  # Set the field as not required
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Units e.g., 50gms'}),
    )

    class Meta:
        model = Product
        fields = ['product_code', 'title', 'price', 'min_price', 'image', 'category', 'quantity', 'units', 'brand', 'expiry_date']

        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Code'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Product Price'}),
            'min_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Product Min Price'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': 'image/*', 'placeholder': 'Product Display Image'}),
            'category': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Product Category'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity (number of products)'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Brand'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Expiry Date', 'required': False}),
        }

        labels = {
            'product_code': 'Product Code',
            'title': 'Product Name',
            'price': 'Product Price',
            'min_price': 'Product Min Price',
            'image': 'Product Display Image',
            'category': 'Product Category',
            'quantity': 'Quantity (number of products)',
            'units': 'Units (e.g., 50gms)',
            'brand': 'Product Brand',
            'expiry_date': 'Expiry Date',
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

class BuyerForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['phone_number', 'first_name', 'last_name']

        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

        labels = {
            'phone_number': 'Phone Number',
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }