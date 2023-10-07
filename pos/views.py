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
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.template.loader import get_template
from io import BytesIO
from reportlab.lib.pagesizes import landscape
from xhtml2pdf import pisa





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

    # Initialize cart_items and total_cost to None
    cart_items = None
    total_cost = 0.0

    # Check if the user is authenticated and has a cart
    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Calculate the total cost of items in the cart
            total_cost = user_cart.cartitem_set.aggregate(total_cost=Sum(models.F('product__price') * models.F('quantity')))['total_cost'] or 0.0

            # Update the total_cost field in the Cart model
            user_cart.total_cost = total_cost
            # user_cart.total_payable =total_cost
            user_cart.save()

            # Retrieve the cart items associated with the cart
            cart_items = user_cart.cartitem_set.all()

    # Retrieve all buyers and apply filtering if provided
    buyers = Buyer.objects.all()
    buyer_name_or_phone = request.GET.get('buyer_name')  # Get the search query

    if buyer_name_or_phone:
        # Apply filter by buyer name or phone number
        buyers = buyers.filter(Q(first_name__icontains=buyer_name_or_phone) | Q(last_name__icontains=buyer_name_or_phone) | Q(phone_number__icontains=buyer_name_or_phone))

    else:
    # If no filter provided, set 'buyers' to an empty queryset
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
    cart = Cart.objects.get(user=request.user)
    vat = cart.total_payable - cart.total_cost

   


    context = {
        'carts': cart,
        'cart': cart_items,
        'total': total_cost,
        'products': products,
        'categories': categories,
        'buyers': buyers,
        'payment_methods': payment_methods,
        'vat':vat
        
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

from django.http import FileResponse
from reportlab.pdfgen import canvas
import io

from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from django.utils import timezone  # Import timezone

# ... (previous code) ...

def generate_pdf_receipt(sale):
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
    sale_date = "Date: 2023-10-10"
    shop_pin = "Shop PIN: 1234"
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
    total_vat_text = f"Total VAT: {sale.vat:.2f}"
    total_payable_text = f"Total Payable: {sale.total_amount:.2f}"
    total_paid_text = f"Total Paid: {sale.total_paid:.2f}"

    draw_centered_text(p, total_vat_text, total_vat_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, total_payable_text, total_payable_y_position, page_width, "Helvetica", 10)
    draw_centered_text(p, total_paid_text, total_paid_y_position, page_width, "Helvetica", 10)

    # Draw double-dotted lines below the totals
    p.setDash(3, 3)  # Set the dash pattern for the lines
    p.line(x_centered + padding, total_paid_y_position - 10, x_centered + receipt_width - padding, total_paid_y_position - 10)

    # Add a line for "You were served by"
    served_by_y_position = total_paid_y_position - 20
    draw_centered_text(p, "You were served by: John Doe", served_by_y_position, page_width, "Helvetica", 10)

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="receipt.pdf")

def draw_centered_text(pdf_canvas, text, y_position, page_width, font_name, font_size):
    # Calculate the x-position for centering the text
    x_centered = (page_width - pdf_canvas.stringWidth(text, font_name, font_size)) / 2
    pdf_canvas.setFont(font_name, font_size)
    pdf_canvas.drawString(x_centered, y_position, text)



def checkout(request):
    # Retrieve the user's cart
    user_cart = get_object_or_404(Cart, user=request.user)

    # Check if the cart is not empty
    if user_cart.products.exists():
        try:
            # Calculate VAT based on your business logic (e.g., 16% VAT)
            vat_rate = Decimal(0.16)  # 16% VAT
            vat_amount = user_cart.total_cost * vat_rate

            # Create a new sale and update the VAT field
            sale = Sale.objects.create(
                user=request.user,
                total_amount=user_cart.total_cost,  # Excluding VAT
                vat=vat_amount,  # Set the VAT amount
                total_paid=user_cart.total_payable,  # Including VAT
            )

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
            pdf_buffer = generate_pdf_receipt(sale)

            # Serve the PDF for download
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt.pdf"'

            return response

        except Exception as e:
            messages.error(request, f'An error occurred during checkout: {str(e)}')
            return redirect('pos:cart')
    else:
        messages.warning(request, 'Your cart is empty. Please add items to your cart before checking out.')

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
    


def sales_h(request):
    # Get the current date
    current_date = datetime.datetime.now()

    # Calculate the week number for the current date
    current_week_number = current_date.strftime("%U")

    try:
        # Retrieve the current week object from the Week model
        current_week = Week.objects.get(
            month__year__year=current_date.year,
            month__month=current_date.month,
            week_number=current_week_number
        )
        
        # Retrieve the days of the current week related to the current_week object
        days_of_week = Day.objects.filter(week=current_week)
        
        # Retrieve all sales data for the current week
        sales_for_current_week = Sale.objects.filter(
            sale_date__gte=days_of_week[0].date,  # Start date of the week
            sale_date__lte=days_of_week[6].date   # End date of the week
        )
    except (Week.DoesNotExist, Day.DoesNotExist):
        # Handle the case where the Week or Day object does not exist for the current week
        current_week = None
        days_of_week = None
        sales_for_current_week = None

    # Initialize a list to store sales data for each day
    sales_data = []

    # Calculate the total sales amount for each day of the week
    if days_of_week:
        for day in days_of_week:
            sales_data.append({
                'day_of_week': day.day_of_week,
                'sales_amount': day.sales_amount,
            })

    # Convert sales_data list to JSON using the custom DecimalEncoder
    sales_data_json = json.dumps(sales_data, cls=DecimalEncoder)
    print(sales_data_json)

    today = timezone.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)


    top_products = SaleItem.objects.filter(
        sale__sale_date__gte=start_of_week,
        sale__sale_date__lte=end_of_week
    ).values('product__title', 'unit_price').annotate(
        total_quantity=Sum('quantity_sold')
    ).order_by('-total_quantity')[:5]  # Get the top 5 products

    # You can pass the current_week, days_of_week, and sales_for_current_week to your template for rendering
    context = {
        'current_week': current_week,
        'days_of_week': days_of_week,
        'sales_data': sales_data_json,  # Include JSON-encoded sales data for the bar graph
        'weekly_sales': sales_for_current_week,  # Include all sales for the current week
        'top_products': top_products,
    }

    return render(request, 'pos/sales_h.html', context)

