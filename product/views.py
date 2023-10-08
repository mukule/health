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
    all_products = Product.objects.all()
    categories = Category.objects.all()

    # Filter by category if provided in GET parameters
    category_param = request.GET.get('category')
    if category_param:
        all_products = all_products.filter(category__name=category_param)

    # Filter by product name if provided in GET parameters
    product_name_param = request.GET.get('product_name')
    if product_name_param:
        all_products = all_products.filter(title__icontains=product_name_param)

    # Paginate the products by 10 per page
    paginator = Paginator(all_products, 10)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Calculate the total amount for the stock
    total_stock_value = all_products.aggregate(
        total_amount=Sum(ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField()))
    )['total_amount'] or 0

    return render(request, 'product/stock.html', {
        'products': products,
        'categories': categories,
        'stock_value': total_stock_value,
        'category_param': category_param,
        'product_name_param': product_name_param,
    })



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

    total_stock_value = products.annotate(
        total_value=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
    ).aggregate(total_amount=Sum('total_value'))['total_amount'] or 0

    # Update the stock_value field in the StockTake model
    stock_take.stock_value = total_stock_value
    stock_take.save()


    # Create StockTakeItem instances for each product with quantity counted as 0
    for product in products:
        StockTakeItem.objects.create(stock_take=stock_take, product=product, quantity_counted=0)

    # Redirect to a success page or another appropriate URL
    print(total_stock_value)
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

            # Recalculate the value based on the updated StockTakeItem instances
            updated_value = StockTakeItem.objects.filter(stock_take=stock_take).aggregate(
                total_value=Sum(F('quantity_counted') * F('product__price'), output_field=DecimalField())
            )['total_value'] or 0

            # Update the value field in the StockTake model
            stock_take.value = updated_value

            # Calculate the difference
            stock_take.difference = stock_take.value - stock_take.stock_value

            # Check if stock is balanced and update the stock_balanced field
            if stock_take.value == stock_take.stock_value:
                stock_take.stock_balanced = True
            else:
                stock_take.stock_balanced = False

            # Save the changes to the StockTake model
            stock_take.save()

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


from datetime import datetime
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from .models import Product, SaleItem

from django.db.models import F

def stock_movement(request):
    # Retrieve all products
    all_products = Product.objects.all()

    # Filter sales items by date range if provided in GET parameters
    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')

    if start_date_param and end_date_param:
        try:
            # Convert start_date and end_date to datetime objects with time components
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

            # Convert the start and end dates to the timezone used in the Sale model
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

            # Filter sales items within the specified date range
            sales_items = SaleItem.objects.filter(sale__sale_date__range=(start_date, end_date))
        except ValueError:
            # Handle invalid date format
            messages.warning(request, 'Invalid date format. Please use YYYY-MM-DD format.')
    else:
        # If no date range is provided, get all sales items
        sales_items = SaleItem.objects.all()

    # Calculate the total quantity sold for each product
    product_sales = []
    for product in all_products:
        sales_for_product = sales_items.filter(product=product)
        total_quantity_sold = sales_for_product.aggregate(total_quantity_sold=Sum('quantity_sold'))['total_quantity_sold'] or 0
        product_sales.append({
            'product': product,
            'total_quantity_sold': total_quantity_sold,
        })

    product_sales = sorted(product_sales, key=lambda x: x['total_quantity_sold'], reverse=True)


    # Pass the product_sales data and date range to the template
    context = {
        'product_sales': product_sales,
        'start_date': start_date_param,
        'end_date': end_date_param,
    }

    return render(request, 'product/stock_movement.html', context)

def suppliers(request):
    suppliers = Supplier.objects.all()
    context = {'suppliers': suppliers}
    return render(request, 'product/suppliers.html', context)

def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product:suppliers')  # Redirect to the supplier list view after successful creation
    else:
        form = SupplierForm()
    
    context = {'form': form}
    return render(request, 'product/supplier_form.html', context)