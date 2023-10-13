from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from product.models import *
from pos.models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json 
from django.utils import timezone
from datetime import date
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse
from reportlab.pdfgen import canvas
import io
import usb.core
from escpos.printer import Usb
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.db.models import Sum, F
from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.utils import timezone  # Import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings

receipts_storage = FileSystemStorage(location=settings.MEDIA_ROOT)


def period(request):
    # Get the current year, month, and week number
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month
    current_week_number = current_date.isocalendar()[1]

    # Check if the current year exists in the Year model
    year, created = Year.objects.get_or_create(year=current_year)
    
    # Check if the current month exists in the Month model for the current year
    month, created = Month.objects.get_or_create(year=year, month=current_month)
    
    # Attempt to get the current week
    try:
        current_week = Week.objects.get(month=month, week_number=current_week_number)
    except Week.DoesNotExist:
        # Create the current week if it doesn't exist
        current_week = Week.objects.create(month=month, week_number=current_week_number)

    # Check if the days of the current week are already created
    if not Day.objects.filter(week=current_week).exists():
        # Create the days of the current week and set their dates
        current_date_in_week = current_date - timedelta(days=current_date.weekday())  # Calculate the start date (Monday) of the current week
        for day_number in range(7):
            day, created = Day.objects.get_or_create(
                week=current_week,
                day_of_week=current_date_in_week.strftime('%A'),
            )
            day.date = current_date_in_week
            day.save()
            current_date_in_week += timedelta(days=1)

    # Calculate sales amount for the current week, current month, and current year
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    sales_week = Sale.objects.filter(
        sale_date__gte=start_of_week,
        sale_date__lte=end_of_week
    ).aggregate(total_sales_week=Sum('total_amount'))['total_sales_week'] or 0.0
    
    sales_month = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total_sales_month=Sum('total_amount'))['total_sales_month'] or 0.0
    
    sales_year = Sale.objects.filter(
        sale_date__year=current_year
    ).aggregate(total_sales_year=Sum('total_amount'))['total_sales_year'] or 0.0
    
    # Update the sales amounts for the current week, current month, and current year
    current_week.sales_amount = sales_week
    current_week.save()
    
    month.sales_amount = sales_month
    month.save()
    
    year.sales_amount = sales_year
    year.save()

    return HttpResponse(status=200)



@login_required  # Require authentication to access this view
def index(request):
    # Call the period function to ensure the current year exists
    period(request)

    # Retrieve all products from the database
    products = Product.objects.all()

    # Apply category filter if selected
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply title search filter if provided
    title = request.GET.get('title')
    if title:
        products = products.filter(title__icontains=title)

    # Retrieve all categories
    categories = Category.objects.all()

    # Initialize cart_items, total_cost, vat, total_payable, and points to 0
    cart_items = None
    total_cost = 0
    vat = 0
    total_payable = 0
    points = 0

    # Check if the user is authenticated and has a cart
    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Calculate the total cost of items in the cart
            total_cost = round(user_cart.cartitem_set.aggregate(
                total_cost=Coalesce(
                    Sum(F('product__price') * F('quantity'), output_field=DecimalField()),
                    Decimal('0.00')
                )
            )['total_cost'])

            # Calculate points for each 100 shillings of total cost
            points = total_cost // 100

            # Update the total_cost field in the Cart model
            user_cart.total_cost = total_cost

            # Check if "Add VAT" is True in the cart
            if user_cart.add_vat:
                vat_rate = Decimal('0.16')  # 16% VAT rate
                vat = round(total_cost * vat_rate)
                total_payable = total_cost + vat
            else:
                vat = 0
                total_payable = total_cost

            user_cart.vat = vat
            user_cart.total_payable = total_payable
            user_cart.points = points
            user_cart.save()

            # Retrieve the cart items associated with the cart
            cart_items = user_cart.cartitem_set.all()

    # Retrieve all buyers and apply filtering if provided
    buyers = Buyer.objects.all()
    buyer_name_or_phone = request.GET.get('buyer_name')  # Get the search query
    

    if buyer_name_or_phone:
        # Apply filter by buyer name or phone number
        filtered_buyers = buyers.filter(Q(first_name__icontains=buyer_name_or_phone) | Q(last_name__icontains=buyer_name_or_phone) | Q(phone_number__icontains=buyer_name_or_phone))

        if filtered_buyers.exists():
            # If there are filtered buyers, update the cart's buyer
            user_cart.buyer = filtered_buyers.first()
            user_cart.save()
            # Update the buyers queryset with filtered_buyers
            buyers = filtered_buyers
        else:
            # If no matching buyers found, set 'buyers' to an empty queryset
            buyers = Buyer.objects.none()
    else:
        # If no filter provided, set 'buyers' to all buyers
        buyers = Buyer.objects.none()

    # Pagination for products
    paginator = Paginator(products, 12)  # 12 products per page
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results
        products = paginator.page(paginator.num_pages)

    payment_methods = PaymentMethod.objects.all()

    
    context = {
        'carts': user_cart,
        'cart': cart_items,
        'total': total_cost,
        'products': products,
        'categories': categories,
        'buyers': buyers,
        'payment_methods': payment_methods,
        'vat': vat,
        'total_payable': total_payable,
    }

    return render(request, 'pos/index.html', context)




@login_required
def toggle_add_vat(request):
    # Get the user's cart
    cart = Cart.objects.get(user=request.user)

    # Toggle the 'add_vat' flag
    cart.add_vat = not cart.add_vat

    # Calculate total_payable based on the 'add_vat' flag with a 16% VAT rate
    if cart.add_vat:
        vat_rate = Decimal(0.16)  # 16% VAT
        cart.total_payable = cart.total_cost + (cart.total_cost * vat_rate)
    else:
        cart.total_payable = cart.total_cost

    # Save the cart
    cart.save()

    return redirect('pos:index')




@login_required
def add_to_cart(request, product_id, quantity=1):
    # Retrieve the product based on the product_id or handle errors if it doesn't exist
    product = get_object_or_404(Product, pk=product_id)

    # Check if the product is out of stock
    if product.quantity <= 0:
        # Handle the case where the product is out of stock
        messages.error(request, 'This product is out of stock.')
        return redirect('pos:index')  # Redirect to the product list page or another appropriate URL

    # Retrieve or create the user's cart using the custom user model
    User = get_user_model()  # Get the custom user model
    user = User.objects.get(username=request.user.username)  # Assuming the user is authenticated
    cart, created = Cart.objects.get_or_create(user=user)

    # Retrieve the cart item for the product or create it if it doesn't exist
    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)

    # Check if adding the specified quantity exceeds the available quantity
    if cart_item.quantity is not None and cart_item.quantity + quantity > product.quantity:
        # Handle the case where there isn't enough quantity available
        messages.error(request, 'There is not enough quantity available for this product.')
        return redirect('pos:index')  # Redirect to the product list page or another appropriate URL

    # If there is enough quantity available, update the cart
    if cart_item.quantity is not None:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    # Show a success message with the product title and quantity
    messages.success(request, f'Added {quantity} {product.title} to cart successfully!')

    # Redirect to the cart or another appropriate URL
    return redirect('pos:index')  # Replace 'cart' with your cart URL name

from django.db.models import Sum

def cart(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Retrieve the user's cart
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Calculate the total cost of items in the cart
            total_cost = user_cart.cartitem_set.aggregate(total_cost=Sum(models.F('product__price') * models.F('quantity')))['total_cost'] or 0.0

            # Update the total_cost field in the Cart model
            user_cart.total_cost = total_cost
            user_cart.save()

            # Retrieve the cart items associated with the cart
            cart_items = user_cart.cartitem_set.all()

            context = {
                'cart': cart_items,
                'total': user_cart.total_cost,
            }

            return render(request, 'pos/cart.html', context)
    
    # Handle the case where the user is not authenticated or there's no cart
    # For example, redirect to a login page or show a message
    return redirect('users:login')

    
def increment_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    # Check if incrementing the quantity exceeds the product's available quantity
    if cart_item.quantity < cart_item.product.quantity:
        cart_item.quantity += 1
        cart_item.save()
    else:
        # If incrementing is not allowed, show an error message
        messages.error(request, "Cannot increase quantity beyond available quantity.")

    return redirect('pos:index')

def decrement_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the quantity is greater than 1 before decrementing
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    
    return redirect('pos:index')

def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('pos:index')





def generate_pdf_receipt(sale, served_by_username):
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Define custom page width and height (adjust as needed)
    page_width = 250  # Adjust the page width
    page_height = 500

    # Define the width of the receipt content (adjust as needed)
    receipt_width = 200  # You can customize the width

    # Calculate the x-position for centering the text
    x_centered = (page_width - receipt_width) / 2

    # Calculate the padding for both left and right sides
    padding = 20  # Adjust the padding as needed

    # Create the PDF object with custom page size (width x height)
    p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Set the font and font size for the title
    p.setFont("Helvetica-Bold", 12)

    # Reduce the space from which the title starts from the top
    title_y_position = page_height - 50

    # Draw the title centered with padding
    draw_centered_text(p, "Health today", title_y_position, page_width, "Helvetica-Bold", 12)

    # Set the font and font size for the shop details
    p.setFont("Helvetica", 10)

    # Define the content for shop address, sale date, PIN, and sale ID (customize as needed)
    shop_address = "St Ellis Building, City Hall Way, Nairobi"
    contact = "+254794085329 | info@healthtoday.co.ke "
    sale_date = sale.sale_date.strftime("Date: %Y-%m-%d %H:%M:%S") 
    shop_pin = "Shop PIN: P0513834130"
    sale_id = f"CASH SALE: {sale.id}"

    # Calculate the y-positions for other content
    address_y_position = title_y_position - 20
    contact_y_position = address_y_position - 15
    date_y_position = contact_y_position - 15
    pin_y_position = date_y_position - 15
    sale_id_y_position = pin_y_position - 15

    # Draw the shop details centered with padding
    draw_centered_text(p, shop_address, address_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, contact, contact_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, sale_date, date_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, shop_pin, pin_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, sale_id, sale_id_y_position, page_width, "Helvetica", 10)

    # Draw double-dotted lines below the details
    dotted_line_y_position = sale_id_y_position - 10
    p.setDash(3, 3)  # Set the dash pattern for the lines
    p.line(x_centered + padding, dotted_line_y_position, x_centered + receipt_width - padding, dotted_line_y_position)

    # Set the font and font size for sales details headers
    p.setFont("Helvetica", 10)  # No longer bold

    # headers
    sales_details = [
        ["Item", "Qty", "Price", "Total"]
    ]

    # data
    for sale_item in SaleItem.objects.filter(sale=sale):
        product_name = sale_item.product.title
        quantity = sale_item.quantity_sold
        unit_price = sale_item.unit_price
        total_price = quantity * unit_price
        detail = [product_name, quantity, f"{unit_price:.2f}", f"{total_price:.2f}"]
        sales_details.append(detail)

    # Calculate the y-position for sales details
    sales_details_y_position = dotted_line_y_position - 25

    # Create the table without grid lines
    table = Table(sales_details, colWidths=[70, 30, 40, 50], rowHeights=15)
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),  # Text color for the first row (headers)
    ]))

    # Calculate the position to center the table
    table_x_position = (page_width - receipt_width) / 2

    # Calculate the total height of the table
    table_height = len(sales_details) * 15  # Assuming row height is 15

    # Adjust the position to ensure it doesn't go beyond the page
    if sales_details_y_position - table_height < 0:
        sales_details_y_position = table_height

    # Draw the table
    table.wrapOn(p, page_width, page_height)
    table.drawOn(p, table_x_position, sales_details_y_position - table_height)

    # Calculate positions for "Total VAT," "Total Payable," and "Total Paid"
    total_vat_y_position = sales_details_y_position - table_height - 25
    total_payable_y_position = total_vat_y_position - 15
    total_paid_y_position = total_payable_y_position - 15

    # Add text for "Total VAT," "Total Payable," and "Total Paid" from the Sale model
    total_vat_text = f"VAT: {sale.vat:.2f}"
    total_payable_text = f"Total: {sale.total_amount:.2f}"
    total_paid_text = f"Total Paid: {sale.total_paid:.2f}"

    draw_centered_text(p, total_vat_text, total_vat_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, total_payable_text, total_payable_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, total_paid_text, total_paid_y_position, page_width, "Helvetica", 10)

    # Draw double-dotted lines below the totals
    p.setDash(3, 3)  # Set the dash pattern for the lines
    p.line(x_centered + padding, total_paid_y_position - 10, x_centered + receipt_width - padding, total_paid_y_position - 10)

    # Add a line for "You were served by"
    served_by_y_position = total_paid_y_position - 20
    draw_centered_text(p, f"You were served by: {served_by_username}", served_by_y_position, page_width, "Helvetica", 10)


    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="receipt.pdf"'
    return response

def draw_centered_text(pdf_canvas, text, y_position, page_width, font_name, font_size):
    # Calculate the x-position for centering the text
    x_centered = (page_width - pdf_canvas.stringWidth(text, font_name, font_size)) / 2
    pdf_canvas.setFont(font_name, font_size)
    pdf_canvas.drawString(x_centered, y_position, text)

from django.db import transaction

@transaction.atomic
def checkout(request):
    try:
        # Retrieve the user's cart
        user_cart = get_object_or_404(Cart, user=request.user)

        # Check if the cart is not empty
        if user_cart.products.exists():
            # Calculate VAT based on your business logic (e.g., 16% VAT)
            if user_cart.add_vat:
                vat_rate = Decimal(0.16)  # 16% VAT
                vat_amount = user_cart.total_cost * vat_rate
            else:
                vat_amount = Decimal(0.0)  # No VAT

            # Create a new sale and update the VAT field
            sale = Sale.objects.create(
                user=request.user,
                total_amount=user_cart.total_cost,  # Excluding VAT
                vat=vat_amount,  # Set the VAT amount
                total_paid=user_cart.total_payable,  # Including VAT
                buyer=user_cart.buyer  # Associate the sale with the buyer from the cart
            )

            # Update buyer's points (assuming each 100 shillings gives 1 point)
            buyer = user_cart.buyer
            if buyer:
                buyer.points += user_cart.points
                buyer.save()

            # Iterate over cart items and create sale items
            for cart_item in user_cart.cartitem_set.all():
                product = cart_item.product
                quantity_sold = cart_item.quantity
                unit_price = product.price

                # Create a sale item
                sale_item = SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity_sold=quantity_sold,
                    unit_price=unit_price
                )
                sale_item.save()

                # Update the product quantity
                product.quantity -= quantity_sold
                product.save()

            # Clear the user's cart after a successful sale
            user_cart.products.clear()
            user_cart.total_cost = 0
            user_cart.save()

            # Update the Day model for the current day
            sale_date = sale.sale_date.date()
            today = sale_date.strftime("%A")  # Get the current day of the week
            current_day = Day.objects.get(
                week__month__year__year=sale_date.year,
                week__month__month=sale_date.month,
                week__week_number=sale_date.isocalendar()[1],
                day_of_week=today
            )
            current_day.sales.add(sale)
            current_day.sales_amount += sale.total_amount
            current_day.save()

            # Generate the PDF receipt
           
            pdf_data = generate_pdf_receipt(sale, request.user.username)

# Return the PDF as a response
            return pdf_data

        else:
            messages.warning(request, 'Your cart is empty. Please add items to your cart before checking out.')

    except Exception as e:
        messages.error(request, f'An error occurred during checkout: {str(e)}')

    return redirect('pos:cart')




def sales(request):
    # Get the current datetime with timezone information
    current_datetime = timezone.now()

    # Get the current date without the time portion
    current_date = current_datetime.date()
    print(current_date)

    # Calculate the start and end of the current day
    start_of_day = timezone.make_aware(timezone.datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0))
    end_of_day = timezone.make_aware(timezone.datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59))

    # Retrieve a list of sales records for the current date
    sales = Sale.objects.filter(sale_date__range=(start_of_day, end_of_day)).order_by('-sale_date')

    # Calculate total sales amount for the current date
    total_sales_amount = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
  

    # Create a Paginator object with 10 items per page
    paginator = Paginator(sales, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page number
    page = paginator.get_page(page_number)

    # Prepare data for a bar chart displaying total sales amounts for the current date
    sale_ids = [sale.id for sale in sales]
    total_amounts = [float(sale.total_amount) for sale in sales]

    # Convert the data to JSON format for use in JavaScript
    sales_data_json = json.dumps({'sale_ids': sale_ids, 'total_amounts': total_amounts})
    print(sales_data_json)

    context = {
        'sales': page,
        'total_sales_amount': total_sales_amount,
        'sales_data_json': sales_data_json,
        'date':current_date
    }

    return render(request, 'pos/sales.html', context)

def sale(request, sale_id):
    # Retrieve the sale object for the given sale_id or return a 404 if not found
    sale = get_object_or_404(Sale, id=sale_id)

    # Now, you can access the related SaleItems for this sale using sale.saleitem_set.all()
    sale_items = sale.saleitem_set.all()

    current_datetime = timezone.now()

    # Get the current date without the time portion
    current_date = current_datetime.date()

    # Calculate the start and end of the current day
    start_of_day = timezone.make_aware(timezone.datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0))
    end_of_day = timezone.make_aware(timezone.datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59))

    # Retrieve a list of sales records for the current date
    sales = Sale.objects.filter(sale_date__range=(start_of_day, end_of_day)).order_by('-sale_date')

    # Calculate total sales amount for the current date
    total_sales_amount = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Create a Paginator object with 10 items per page
    paginator = Paginator(sales, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page number
    page = paginator.get_page(page_number)

    # Prepare data for a bar chart displaying total sales amounts for the current date
    sale_ids = [sale.id for sale in sales]
    total_amounts = [float(sale.total_amount) for sale in sales]  # Convert Decimal to float

    # Prepare data for a chart displaying sold items
    sold_item_labels = [item.product.title for item in sale_items]
    sold_item_quantities = [item.quantity_sold for item in sale_items]

    # Convert the data to JSON format for use in JavaScript
    sales_data_json = json.dumps({'sale_ids': sale_ids, 'total_amounts': total_amounts})
    sold_items_data_json = json.dumps({'labels': sold_item_labels, 'quantities': sold_item_quantities})

    context = {
        'sale': sale,
        'date':current_date,
        'today_sales': sale_items,
        'sales': page,
        'total_sales_amount': total_sales_amount,
        'sales_data_json': sales_data_json,  # Pass the total sales data to the template
        'sold_items_data_json': sold_items_data_json,  # Pass the sold items data to the template
    }

    return render(request, 'pos/sales.html', context)


import json
from decimal import Decimal
from datetime import timedelta

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)
  
from datetime import datetime, timedelta  # Import datetime from Python's datetime module

from django.db.models import *


def sales_h(request):
    # Retrieve all sales data (unfiltered)
    sales_data = Sale.objects.all().order_by('-sale_date')

    # Filter sales by date range if provided in GET parameters
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

            # Filter sales within the specified date range
            sales_data = sales_data.filter(sale_date__range=(start_date, end_date))
        except ValueError:
            # Handle invalid date format
            messages.warning(request, 'Invalid date format. Please use YYYY-MM-DD format.')

    # Calculate the total amounts
    total_sales_amount = sales_data.aggregate(total_sales=Sum('total_amount'))['total_sales'] or Decimal('0.0')
    total_vat_amount = sales_data.aggregate(total_vat=Sum('vat'))['total_vat'] or Decimal('0.0')
    total_paid_amount = sales_data.aggregate(total_paid=Sum('total_paid'))['total_paid'] or Decimal('0.0')

    # Get sold items for each sale
    sold_items = SaleItem.objects.filter(sale__in=sales_data)

    # Aggregate total quantity sold for each product
    product_sales = sold_items.values('product__title', 'product__category__name').annotate(
        total_quantity_sold=Sum('quantity_sold')
    )

    # Calculate total sales amount for each category
    category_sales = sold_items.values('product__category__name').annotate(
        total_category_sales=Sum(F('quantity_sold') * F('unit_price'), output_field=DecimalField())
    )

    # Prepare chart data
    chart_data = []
    for category in category_sales:
        chart_data.append({
            'category': category['product__category__name'],
            'total_sales': category['total_category_sales'],
        })

    # Convert chart data to JSON
    chart_data_json = json.dumps(chart_data, cls=DecimalEncoder)
    print(chart_data_json)

   

    context = {
        'sales_page': sales_data,          # Include paginated sales data
        'total': total_sales_amount,
        'total_vat': total_vat_amount,
        'total_paid': total_paid_amount,
        'product_sales': product_sales,
        'chart_data': chart_data_json,
    }

    return render(request, 'pos/sales_h.html', context)


