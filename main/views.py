from django.shortcuts import render, redirect, get_object_or_404
from product.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import *
from django.contrib import messages
from product.forms import *
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required


def is_superuser_admin_cashier(user):
    return user.is_superuser or (user.access_level in [1, 3])


def index(request):
    categories = Category.objects.all()

    # Retrieve all products
    products_list = Product.objects.all()

    title_filter = request.GET.get('title')

    category_id = request.GET.get('category')
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products_list = products_list.filter(category=selected_category)
    else:
        selected_category = None

    if title_filter:
        products_list = products_list.filter(title__icontains=title_filter)

    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    # Prefetch related products for each category to avoid multiple database queries
    categories_with_products = []
    for category in categories:
        category_products = products_list.filter(category=category)
        categories_with_products.append(
            {'category': category, 'products': category_products})

    slider1 = Promotion.objects.all()
    slider2 = Product.objects.order_by('-price')[:5]
    about = About.objects.all()
    available_products = Product.objects.filter(quantity__gt=0)

    context = {
        'categories': categories,
        'products': products,
        's1': slider1,
        's2': slider2,
        'selected_category': selected_category,
        'about': about,
        'ap': available_products,
        'categories_with_products': categories_with_products,  # Add this to context
    }

    return render(request, 'main/index.html', context)


def product_detail(request, product_id):
    # Retrieve product object or return 404 error if not found
    product = get_object_or_404(Product, pk=product_id)

    # Retrieve the category of the product
    category = product.category

    # Retrieve other products in the same category excluding the current product
    other_products = Product.objects.filter(
        category=category).exclude(pk=product_id)

    print(other_products)

    # Render template with product details and other products in the same category
    return render(request, 'main/product_detail.html', {'product': product, 'other_products': other_products})


@login_required
@user_passes_test(is_superuser_admin_cashier, login_url='users:not_authorized')
def create_buyer(request):
    if request.method == 'POST':
        form = BuyerForm(request.POST)
        if form.is_valid():
            # Create a new Buyer instance and save it to the database
            buyer = form.save()
            # Replace 'buyer_list' with the URL name for listing buyers
            return redirect('main:buyers')
    else:
        form = BuyerForm()

    context = {
        'form': form,
    }

    return render(request, 'main/create_buyer.html', context)


@login_required
@user_passes_test(is_superuser_admin_cashier, login_url='users:not_authorized')
def buyers(request):
    buyers = Buyer.objects.all()

    context = {
        'buyers': buyers,
    }

    return render(request, 'main/buyers.html', context)


def print_and_cut(request):
    return render(request, 'main/receipt.html')


def create_about(request):
    if request.method == 'POST':
        form = AboutForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or do something else
            return redirect('pos:about')
    else:
        form = AboutForm()

    return render(request, 'main/create_about.html', {'form': form})
