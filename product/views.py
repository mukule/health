from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product Category created successfully, You May Add Another one.')
            return redirect('product:create_category')  # Redirect to the category list view
    else:
        form = CategoryForm()
    
    return render(request, 'product/create_category.html', {'form': form})

def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully. You may add another one.')
            return redirect('product:create_product')  # Redirect to the product creation view
        else:
            messages.error(request, 'Error creating the product. Please check the form and try again.')
    else:
        form = ProductForm()
    
    return render(request, 'product/create_product.html', {'form': form})

def products(request):
    categories = Category.objects.all()  # Query all categories from the database
    selected_category = None
    title_query = request.GET.get('title')

    # Check if a category filter is specified in the URL
    category_id = request.GET.get('category')
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products_list = Product.objects.filter(category=selected_category)
    else:
        # No category filter specified, fetch all products
        products_list = Product.objects.all()

    # Apply title filter if a search query is provided
    if title_query:
        products_list = products_list.filter(title__icontains=title_query)

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

    return render(request, 'product/products.html', {'products': products, 'categories': categories, 'selected_category': selected_category})