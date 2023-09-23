from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import *
from users.models import *

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

def edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product Category updated successfully.')
            return redirect('product:products')  # Redirect to the category list view
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'product/edit_category.html', {'form': form, 'category': category})

def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

  
    category.delete()
    messages.success(request, 'Product Category deleted successfully.')
    return redirect('product:products')  # Redirect to the category list view
    
    
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

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product:products')  # Redirect to the product list view
        else:
            messages.error(request, 'Error updating the product. Please check the form and try again.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'product/edit_product.html', {'form': form, 'product': product})


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

   
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('product:products')  # Redirect to the product list view
  

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




def stock(request):
    # Retrieve all products
    products = Product.objects.all()

    # Calculate the total amount for the stock
    total_stock_value = products.annotate(
        total_value=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
    ).aggregate(total_amount=Sum('total_value'))['total_amount'] or 0

    return render(request, 'product/stock.html', {'products': products, 'stock_value': total_stock_value})


def low_stock(request):
    low_stock_products = Product.objects.filter(quantity__lte=5)
    low_stock_count = low_stock_products.count()  # Count the low stock products
    return render(request, 'product/low_stock.html', {'products': low_stock_products, 'products_count': low_stock_count})

def out_of_stock(request):
    out_of_stock_products = Product.objects.filter(quantity=0)
    out_of_stock_count = out_of_stock_products.count()  # Count the out of stock products
    return render(request, 'product/out_of_stock.html', {'products': out_of_stock_products, 'products_count': out_of_stock_count})
def create_stock_take(request):
    # Check for permissions or authentication if necessary

    # Create a new stock take with the current date
    stock_take = StockTake.objects.create(stock_date=timezone.now(), user=request.user)

    # Get all products
    products = Product.objects.all()

    # Create StockTakeItem instances for each product with quantity counted as 0
    for product in products:
        StockTakeItem.objects.create(stock_take=stock_take, product=product, quantity_counted=0)

    # Redirect to a success page or another appropriate URL
    return redirect('product:stocks')

def stocks(request):
    # Retrieve all stock takes from the database
    stock_takes = StockTake.objects.all()
    
    # Pass the stock takes to the template for rendering
    return render(request, 'product/stocks.html', {'stocks': stock_takes})
def stock_detail(request, stock_take_id):
    # Retrieve the specific stock take based on the stock_take_id or show a 404 page if not found
    stock_take = get_object_or_404(StockTake, pk=stock_take_id)

    # Retrieve all products associated with this stock take
    products_in_stock_take = stock_take.products.all()

    # Pass the stock take and products to the template for rendering
    return render(request, 'product/stock_detail.html', {
        'stock': stock_take,
        'stock_products': products_in_stock_take,
    })

def update_stock_take(request, stock_take_id):
    stock_take = get_object_or_404(StockTake, pk=stock_take_id)
    
    if request.method == 'POST':
        form = StockTakeItemForm(request.POST)
        if form.is_valid():
            stock_take_item = form.save(commit=False)
            stock_take_item.stock_take = stock_take
            stock_take_item.save()
            return redirect('your_success_url_name')
    else:
        form = StockTakeItemForm()

    return render(request, 'your_template.html', {'form': form, 'stock_take': stock_take})



def update_stock_take_item(request, stock_take_id, stock_take_item_id):
    # Retrieve the specific StockTake and StockTakeItem instances
    stock_take = get_object_or_404(StockTake, pk=stock_take_id)
    stock_take_item = get_object_or_404(StockTakeItem, pk=stock_take_item_id)

    if request.method == 'POST':
        # Create a form for updating the quantity counted
        form = StockTakeItemUpdateForm(request.POST, instance=stock_take_item)
        if form.is_valid():
            # Update and save the StockTakeItem
            form.save()
            # Redirect to the stock take detail page or another appropriate URL
            return redirect('product:stock_detail', stock_take_id=stock_take.id)

    else:
        # Create a form for rendering
        form = StockTakeItemUpdateForm(instance=stock_take_item)

    context = {
        'stock': stock_take,
        'stock_product': stock_take_item,
        'form': form,
    }

    return render(request, 'product/update_stock.html', context)
