from django.shortcuts import render, redirect, get_object_or_404
from product.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import *
from django.contrib import messages

# Create your views here.
def index(request):
    # Retrieve all categories
    categories = Category.objects.all()

    # Retrieve all products
    products_list = Product.objects.all()

    # Handle search filter by title
    title_filter = request.GET.get('title')
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

    return render(request, 'main/index.html', {'categories': categories, 'products': products})