from .models import Promotion
from .forms import PromotionForm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.db.models import F
from .models import Product, SaleItem
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Sum
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import *
from users.models import *
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from .models import Product
from users.decorators import *
from django.core.serializers import serialize
from django.http import JsonResponse
import json



@login_required
@second
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Product Category created successfully, You May Add Another one.')
            # Redirect to the category list view
            return redirect('product:create_category')
    else:
        form = CategoryForm()

    return render(request, 'product/create_category.html', {'form': form})


@login_required
@second
def edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product Category updated successfully.')
            # Redirect to the category list view
            return redirect('product:products')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'product/edit_category.html', {'form': form, 'category': category})


@login_required
@second
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    category.delete()
    messages.success(request, 'Product Category deleted successfully.')
    return redirect('product:products')  # Redirect to the category list view


@login_required
@second
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Product created successfully. You may add another one.')
            # Redirect to the product creation view
            return redirect('product:create_product')
        else:
            messages.error(
                request, 'Error creating the product. Please check the form and try again.')
    else:
        form = ProductForm()

    return render(request, 'product/create_product.html', {'form': form})


@login_required
@second
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            # Redirect to the product list view
            return redirect('product:products')
        else:
            messages.error(
                request, 'Error updating the product. Please check the form and try again.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'product/edit_product.html', {'form': form, 'product': product})


@login_required
@second
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('product:products')  # Redirect to the product list view


@login_required
@second
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


@login_required
@second
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
        total_amount=Sum(ExpressionWrapper(
            F('quantity') * F('price'), output_field=DecimalField()))
    )['total_amount'] or 0

    return render(request, 'product/stock.html', {
        'products': products,
        'categories': categories,
        'stock_value': total_stock_value,
        'category_param': category_param,
        'product_name_param': product_name_param,
    })


@login_required
@third
def low_stock(request):
    low_stock_products = Product.objects.filter(quantity__lte=5)
    low_stock_count = low_stock_products.count()  # Count the low stock products
    return render(request, 'product/low_stock.html', {'products': low_stock_products, 'products_count': low_stock_count})


@login_required
@third
def out_of_stock(request):
    out_of_stock_products = Product.objects.filter(quantity=0)
    # Count the out of stock products
    out_of_stock_count = out_of_stock_products.count()
    return render(request, 'product/out_of_stock.html', {'products': out_of_stock_products, 'products_count': out_of_stock_count})


@login_required
@third
def create_stock_take(request):
    # Check for permissions or authentication if necessary

    # Create a new stock take with the current date
    stock_take = StockTake.objects.create(
        stock_date=timezone.now(), user=request.user)

    # Get all products
    products = Product.objects.all()

    total_stock_value = products.annotate(
        total_value=ExpressionWrapper(
            F('quantity') * F('price'), output_field=DecimalField())
    ).aggregate(total_amount=Sum('total_value'))['total_amount'] or 0

    # Update the stock_value field in the StockTake model
    stock_take.stock_value = total_stock_value
    stock_take.save()

    # Create StockTakeItem instances for each product with quantity counted as 0
    for product in products:
        StockTakeItem.objects.create(
            stock_take=stock_take, product=product, quantity_counted=0)

    # Redirect to a success page or another appropriate URL
    print(total_stock_value)
    return redirect('product:stocks')


@login_required
@third
def stocks(request):
    # Retrieve all stock takes from the database
    stock_takes = StockTake.objects.all()

    # Pass the stock takes to the template for rendering
    return render(request, 'product/stocks.html', {'stocks': stock_takes})


@login_required
@third
def stock_detail(request, stock_take_id):
    stock_take = get_object_or_404(StockTake, pk=stock_take_id)

    # Retrieve all products associated with this stock take
    products_in_stock_take = stock_take.products.all()

    # Pass the stock take and products to the template for rendering
    return render(request, 'product/stock_detail.html', {
        'stock': stock_take,
        'stock_products': products_in_stock_take,
    })


@login_required
@third
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


@login_required
@third
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
                total_value=Sum(F('quantity_counted') *
                                F('product__price'), output_field=DecimalField())
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


@login_required
@second
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
            end_date = datetime.strptime(
                end_date_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

            # Convert the start and end dates to the timezone used in the Sale model
            start_date = timezone.make_aware(
                start_date, timezone.get_current_timezone())
            end_date = timezone.make_aware(
                end_date, timezone.get_current_timezone())

            # Filter sales items within the specified date range
            sales_items = SaleItem.objects.filter(
                sale__sale_date__range=(start_date, end_date))
        except ValueError:
            # Handle invalid date format
            messages.warning(
                request, 'Invalid date format. Please use YYYY-MM-DD format.')
    else:
        # If no date range is provided, get all sales items
        sales_items = SaleItem.objects.all()

    # Calculate the total quantity sold for each product
    product_sales = []
    for product in all_products:
        sales_for_product = sales_items.filter(product=product)
        total_quantity_sold = sales_for_product.aggregate(
            total_quantity_sold=Sum('quantity_sold'))['total_quantity_sold'] or 0
        product_sales.append({
            'product': product,
            'total_quantity_sold': total_quantity_sold,
        })

    product_sales = sorted(
        product_sales, key=lambda x: x['total_quantity_sold'], reverse=True)

    # Pass the product_sales data and date range to the template
    context = {
        'product_sales': product_sales,
        'start_date': start_date_param,
        'end_date': end_date_param,
    }

    return render(request, 'product/stock_movement.html', context)


@login_required
@second
def suppliers(request):
    suppliers = Supplier.objects.all()
    user = request.user
    context = {
        'suppliers': suppliers,
        'user': user
    }
    return render(request, 'product/suppliers.html', context)


@login_required
@second
def supplier_create(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        print(form.data)
        if form.is_valid():
            print(form.data)
            form.save()
            # Redirect to the supplier list view after successful creation
            return redirect('product:suppliers')
        else:
            # Print or log form errors if validation fails
            print(form.errors)
    else:
        form = SupplierForm()
        print(form.data)

    products_by_category = {}
    for category in categories:
        products = Product.objects.filter(category=category)
        products_by_category[category.id] = serialize('json', products)

    context = {
        'form': form,
        'categories': categories,
        'products': products_by_category
    }

    # Add form errors to the context to display them in the template
    if form.errors:
        context['form_errors'] = form.errors

    return render(request, 'product/supplier_form.html', context)


def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            # Redirect to the supplier list view after successful edit
            return redirect('product:suppliers')
        else:
            # Print or log form errors if validation fails
            print(form.errors)
    else:
        form = SupplierForm(instance=supplier)

    products_by_category = {}
    for category in categories:
        products = Product.objects.filter(category=category)
        products_by_category[category.id] = serialize('json', products)

    context = {
        'form': form,
        'categories': categories,
        'products': products_by_category
    }

    # Add form errors to the context to display them in the template
    if form.errors:
        context['form_errors'] = form.errors

    return render(request, 'product/supplier_edit.html', context)


def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    supplier.delete()
    # Redirect to the supplier list view after successful deletion
    return redirect('product:suppliers')


@login_required
@third
def receivings(request):
    supplier = None

    if request.method == 'POST':
        form = ReceivingForm(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']
            product_id = form.cleaned_data['products'].id
            product_quantity = form.cleaned_data['product_quantity']
            product_unit_price = form.cleaned_data['product_unit_price']

            # Create Receiving instance with the logged-in user as the receiver
            receiving = form.save(commit=False)
            receiving.receiver = request.user
            receiving.save()

            # Associate the product with the receiving instance
            product = get_object_or_404(Product, pk=product_id)
            received_product, created = ReceivedProduct.objects.get_or_create(
                receiving=receiving,
                product=product,
                defaults={
                    'product_quantity': product_quantity,
                    'unit_price': product_unit_price
                }
            )

            # Update or create a corresponding Supply instance
            supply, created = Supply.objects.get_or_create(
                supplier=supplier,
                product=product,
                defaults={
                    'price': product_unit_price,
                    'total_amount': product_quantity * product_unit_price,
                    'paid': False
                }
            )

            # Update the product quantity
            product.quantity += product_quantity
            product.save()

            supply.price = product_unit_price
            supply.total_amount = product_quantity * product_unit_price
            supply.paid = False
            supply.save()

            messages.success(
                request, 'Products received and stock updated sucessfully')
            return redirect('pos:received')
    else:
        form = ReceivingForm()
        suppliers = Supplier.objects.all()
        supplier_with_products = {}

        for supplier in suppliers:
            products_for_supplier = supplier.products.all()
            supplier_with_products[supplier.id] = serialize(
                'json', products_for_supplier)

    return render(request, 'product/receiving.html', {'form': form, 'supplier_with_products': supplier_with_products})


def d_product(request):
    title_filter = request.GET.get('title', '')

    # Apply filters if title filter is present
    if title_filter:
        all_products = Product.objects.filter(Q(title__icontains=title_filter))
    else:
        all_products = Product.objects.all()

    context = {
        'products': all_products,
        'title_filter': title_filter,
    }
    return render(request, 'product/d_product.html', context)


@login_required
@third
def dispatch(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = DispatchForm(request.POST)
        if form.is_valid():
            destination = form.cleaned_data['destination']
            reason = form.cleaned_data['reason']
            product_quantity = form.cleaned_data['product_quantity']

            # Check if there are enough products available for dispatch
            if product_quantity > product.quantity:
                messages.error(
                    request, 'Not enough products available for dispatch.')
                return redirect('product:dispatch', product_id=product_id)

            # Create Dispatch instance
            dispatch = Dispatch.objects.create(
                destination=destination,
                reason=reason,
                dispatcher=request.user,
                product=product,
                product_quantity=product_quantity
            )

            # Create DispatchedProduct instance
            DispatchedProduct.objects.create(
                dispatch=dispatch,
                product_quantity=product_quantity
            )

            # Update the quantity field for the dispatched product
            product.quantity -= product_quantity
            product.save()

            messages.success(request, 'Products dispatched successfully.')
            return redirect('product:dispatches')  # Redirect to a success page

    else:
        # For GET requests, initialize the form with the product instance
        form = DispatchForm(initial={'product': product})

    return render(request, 'product/dispatch.html', {'form': form, 'product': product})


@login_required
@third
def dispatches(request):
    dispatches_list = Dispatch.objects.all()
    return render(request, 'product/dispatches.html', {'dispatches_list': dispatches_list})


@login_required
@third
def export_stock(request):
    # Retrieve all products from the database
    products = Product.objects.all()

    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')

    # Generate filename with the current date
    filename = f"products_{datetime.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Create a PDF document
    pdf = SimpleDocTemplate(response, pagesize=letter,
                            leftMargin=20, rightMargin=20)

    # Set up the elements for the PDF
    elements = []

    # Title
    title = "Health Today Products"
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))

    # Table data
    data = [["Product ID", "Product Code", "Title",
             "Brand", "Units", "Price", "Quantity"]]

    for product in products:
        data.append([str(product.id), str(product.product_code), product.title, product.brand,
                     str(product.units), str(product.price), str(product.quantity)])

    # Create the table
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        # Green background for header
        ('BACKGROUND', (0, 0), (-1, 0), '#33B44B'),
        # White text color for header
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        # Left alignment for data cells
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, styles['Heading1'].textColor),
        # Set specific column width and font size for the 'Title' column
        ('COLWIDTH', (2, 0), (2, -1), 1.6 * inch),
        ('FONTSIZE', (0, 0), (-1, -1), 7),  # Set font size for all cells to 7
        ('LEADING', (2, 0), (2, -1), 10),
    ]))

    # Add the table to the elements
    elements.append(table)

    # Build the PDF document with page breaks
    pdf.build(elements, onFirstPage=lambda canvas, doc: None,
              onLaterPages=lambda canvas, doc: canvas.drawString(10, 10, "Continued..."))

    return response


@login_required
@third
def product_promotion(request):
    product_filter = request.GET.get('product_filter')
    title_filter = request.GET.get('title_filter')

    # Ensure that the filters are not None before using them in the query
    product_filter_query = Q(
        product_code__icontains=product_filter) if product_filter else Q()
    title_filter_query = Q(
        title__icontains=title_filter) if title_filter else Q()

    products = Product.objects.filter(
        product_filter_query | title_filter_query)

    context = {
        'products': products,
    }

    return render(request, 'product/p_promotion.html', context)


@login_required
@third
def promotion(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.product = product

            print(promotion)

            # Check if start date is in the past
            if promotion.start_date < timezone.now().date():
                messages.error(
                    request, 'Please check the start date of this promotion. It should not be a date before today.')
                return render(request, 'product/promotion.html', {'form': form, 'product': product})

            # Check for overlapping promotions
            overlapping_promotions = Promotion.objects.filter(
                product=product,
                start_date__lte=promotion.end_date,
                end_date__gte=promotion.start_date
            ).exclude(id=promotion.id)

            if overlapping_promotions.exists():
                messages.error(
                    request, 'This promotion overlaps with an existing promotion. Please choose different dates.')
                return render(request, 'product/promotion.html', {'form': form, 'product': product})

           # Calculate discount percentage
            if promotion.initial_price != 0:
                if promotion.current_price is None:
                    # If current_price is not provided, use the product price
                    promotion.current_price = product.price

                discount_amount = promotion.initial_price - promotion.current_price
                promotion.discount_percentage = round(
                    (discount_amount / promotion.initial_price) * 100)
            else:
                # If initial_price is zero, set discount_percentage to None
                promotion.discount_percentage = None

            promotion.save()

            # Update product price only if current_price is provided
            if promotion.current_price is not None:
                product.price = promotion.current_price
                product.save()
            else:
                # If current_price is not provided, update with the product price
                promotion.current_price = product.price
                promotion.save()

            return redirect('product:promotions')
    else:
        # Set the initial value of current_price to the product price
        initial_current_price = product.price
        form = PromotionForm(
            initial={'product': product, 'current_price': initial_current_price})

    context = {
        'form': form,
        'product': product
    }

    return render(request, 'product/promotion.html', context)


@login_required
@third
def edit_promotion(request, promotion_id):
    promotion = get_object_or_404(Promotion, id=promotion_id)
    product = promotion.product

    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            # Save the form to update promotion details
            promotion = form.save(commit=False)
            # Ensure the correct product is associated with the promotion
            promotion.product = product
            print("After assignment: promotion.product =",
                  promotion.current_price)

            # Check if the start date is in the past
            if promotion.start_date < timezone.now().date():
                messages.error(
                    request, 'Please check the start date of this promotion. It should not be a date before today.')
                return render(request, 'product/promotion.html', {'form': form, 'product': product})

            # Check for overlapping promotions
            overlapping_promotions = Promotion.objects.filter(
                product=product,
                start_date__lte=promotion.end_date,
                end_date__gte=promotion.start_date
            ).exclude(id=promotion.id)

            if overlapping_promotions.exists():
                messages.error(
                    request, 'This promotion overlaps with an existing promotion. Please choose different dates.')
                return render(request, 'product/promotion.html', {'form': form, 'product': product})

            # Update product price with the new price from the promotion before calculating the discount
            product.price = promotion.current_price
            product.save()

            # Calculate discount percentage
            if promotion.initial_price != 0:
                discount_amount = promotion.initial_price - promotion.current_price
                promotion.discount_percentage = round(
                    (discount_amount / promotion.initial_price) * 100)
            else:
                # If initial_price is zero, set discount_percentage to None
                promotion.discount_percentage = None

            # Save the promotion after updating details
            promotion.save()

            return redirect('product:promotions')
    else:
        form = PromotionForm(instance=promotion)

    context = {
        'form': form,
        'promo': promotion
    }

    return render(request, 'product/edit_promotion.html', context)


@login_required
@third
def promotions(request):
    promo = Promotion.objects.all()
    return render(request, 'product/promotions.html', {'promo': promo})


@login_required
@third
def delete_promotion(request, promotion_id):
    # Get the promotion object or return a 404 response if not found
    promotion = get_object_or_404(Promotion, id=promotion_id)

    promotion.delete()
    return redirect('product:promotions')


@login_required
@third
def stock_update(request, stocktake_id):
    stocktake = get_object_or_404(StockTake, pk=stocktake_id)
    stocktake_items = StockTakeItem.objects.filter(stock_take=stocktake)

    for item in stocktake_items:
        # Update product quantity with the counted value
        product = item.product
        product.quantity = item.quantity_counted
        product.save()

    return redirect('pos:index')


def brands(request):
    # Get all unique brands from the Product model
    brands = Product.objects.values('brand').exclude(brand__isnull=True).annotate(count=Count('brand'))

    # You can pass the brands data to the template
    context = {'brands': brands}

    return render(request, 'product/brands.html', context)
