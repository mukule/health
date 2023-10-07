from django.shortcuts import render, redirect, get_object_or_404
from product.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import *
from django.contrib import messages
from product.forms import *


def index(request):
    # Retrieve all categories
    categories = Category.objects.all()

    # Retrieve all products
    products_list = Product.objects.all()

    # Handle search filter by title
    title_filter = request.GET.get('title')
    
    # Check if a category filter is specified in the URL
    category_id = request.GET.get('category')
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products_list = products_list.filter(category=selected_category)
    else:
        selected_category = None

    if title_filter:
        products_list = products_list.filter(title__icontains=title_filter)

    # Paginate the products with 9 products per page
    paginator = Paginator(products_list, 9)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results
        products = paginator.page(paginator.num_pages)

    # Retrieve the first 10 products with the highest quantities
    top_10_products = Product.objects.order_by('-quantity')[:10]

    context = {
        'categories': categories,
        'products': products,
        'top_10_products': top_10_products,
        'selected_category': selected_category,  # Add the selected category to the context
    }

    return render(request, 'main/index.html', context)

def create_buyer(request):
    if request.method == 'POST':
        form = BuyerForm(request.POST)
        if form.is_valid():
            # Create a new Buyer instance and save it to the database
            buyer = form.save()
            return redirect('main:buyers')  # Replace 'buyer_list' with the URL name for listing buyers
    else:
        form = BuyerForm()

    context = {
        'form': form,
    }

    return render(request, 'main/create_buyer.html', context)

def buyers(request):
    buyers = Buyer.objects.all()

    context = {
        'buyers': buyers,
    }

    return render(request, 'main/buyers.html', context)
