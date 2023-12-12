from .models import Supplier
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
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Units e.g., 50gms'}),
    )

    class Meta:
        model = Product
        fields = ['product_code', 'title', 'price', 'min_price', 'image',
                  'category', 'quantity', 'units', 'brand', 'expiry_date']

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
        self.fields['quantity_counted'].widget.attrs.update(
            {'class': 'form-control'})


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


class SupplierForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
        label='Name'
    )

    contact_person = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter contact person'}),
        label='Contact Person'
    )

    email = forms.EmailField(
        max_length=100,
        required=False,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
        label='Email'
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        label='Phone Number'
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': 'Enter address'}),
        label='Address'
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(
            attrs={'class': 'form-control category-selector', 'id': 'id_category_supplied'}),
        label='Category Supplied'
    )

    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.SelectMultiple(
            attrs={'class': 'form-control', 'placeholder': 'Select Category first', 'id': 'id_products_supplied'}),
        label='Products Supplied',
        required=False
    )

    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email',
                  'phone_number', 'address', 'products', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the email and phone_number fields not required
        self.fields['email'].required = False
        self.fields['phone_number'].required = False


class ReceivingForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        widget=forms.Select(
            attrs={'class': 'form-control', 'id': 'supplier-select'}),
        label='Supplier',
        empty_label='Select Supplier'
    )

    products = forms.ChoiceField(
        choices=[('', 'Select Product')],
        widget=forms.Select(
            attrs={'class': 'form-control', 'id': 'products-select'}),
        label='Products',

    )

    product_quantity = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
        label='Product Quantity'
    )

    product_unit_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter unit price'}),
        label='Product Unit Price'
    )

    class Meta:
        model = Receiving
        fields = ['supplier', 'products',
                  'product_quantity', 'product_unit_price']

    def __init__(self, *args, **kwargs):
        super(ReceivingForm, self).__init__(*args, **kwargs)
        self.fields['supplier'].widget.attrs['class'] = 'form-control'
        self.fields['products'].widget.attrs['class'] = 'form-control'
        self.fields['product_quantity'].widget.attrs['class'] = 'form-control'
        self.fields['product_unit_price'].widget.attrs['class'] = 'form-control'


class DispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = ['product', 'product_quantity', 'destination', 'reason']

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(
            attrs={'class': 'form-control', 'id': 'supplier-select'}),
        label='Product',
        empty_label='Select Product'  # Add this line for the placeholder
    )

    product_quantity = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
        min_value=1,
        label='Product Quantity'
    )

    def __init__(self, *args, **kwargs):
        super(DispatchForm, self).__init__(*args, **kwargs)

        # Add a placeholder option for the product select field
        self.fields['product'].widget.attrs['class'] = 'form-control'
        self.fields['product'].widget.attrs['placeholder'] = 'Select Product'
        self.fields['destination'].widget.attrs['class'] = 'form-control'
        self.fields['reason'].widget.attrs['class'] = 'form-control'
        self.fields['product_quantity'].widget.attrs['class'] = 'form-control'


class PromotionForm(forms.ModelForm):
    initial_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter initial price'}),
        label='Initial Price'
    )
    current_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Current price'}),
        label='Current Price'
    )

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD', 'type': 'date'}),
        label='Start Date'
    )

    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD', 'type': 'date'}),
        label='End Date'
    )

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Product'
    )

    class Meta:
        model = Promotion
        fields = ['initial_price', 'current_price',
                  'start_date', 'end_date', 'product']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize widgets, labels, or any other field attributes if needed

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Add custom validation if needed, e.g., ensuring the end date is after the start date
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError(
                "End date must be after the start date.")


class AboutForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    title = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}))

    class Meta:
        model = About
        fields = ['title', 'description']
