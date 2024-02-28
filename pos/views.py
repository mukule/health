from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import subprocess
from PIL import Image as PILImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from users.decorators import *
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models import *
from datetime import timedelta
import json
from django.db import transaction
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
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse
from reportlab.pdfgen import canvas
import io
import usb.core
from escpos.printer import Usb
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.db.models import Sum, F
from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from barcode import generate
from barcode.writer import ImageWriter
receipts_storage = FileSystemStorage(location=settings.MEDIA_ROOT)


@login_required
@third
def period(request):
    # Get the current year, month, and week number
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month
    current_week_number = current_date.isocalendar()[1]

    # Check if the current year exists in the Year model
    year, created = Year.objects.get_or_create(year=current_year)

    # Check if the current month exists in the Month model for the current year
    month, created = Month.objects.get_or_create(
        year=year, month=current_month)

    # Attempt to get the current week
    try:
        current_week = Week.objects.get(
            month=month, week_number=current_week_number)
    except Week.DoesNotExist:
        # Create the current week if it doesn't exist
        current_week = Week.objects.create(
            month=month, week_number=current_week_number)

    # Check if the days of the current week are already created
    if not Day.objects.filter(week=current_week).exists():
        # Create the days of the current week and set their dates
        # Calculate the start date (Monday) of the current week
        current_date_in_week = current_date - \
            timedelta(days=current_date.weekday())
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
@third
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
    total_cost = 0.00
    vat = 0.00
    discount = 0.00
    total_payable = 0.00
    points = 0.00

    # Check if the user is authenticated and has a cart
    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Calculate the total cost of items in the cart
            total_cost = round(user_cart.cartitem_set.aggregate(
                total_cost=Coalesce(
                    Sum(F('product__price') * F('quantity'),
                        output_field=DecimalField()),
                    Decimal('0.00')
                )
            )['total_cost'])

            # Calculate points for each 100 shillings of total cost
            points = total_cost // 100

            # Update the total_cost field in the Cart model
            user_cart.total_cost = total_cost

            # Calculate the discount from the user's cart
            discount = user_cart.discount

            # Apply the discount to the total cost
            total_cost_after_discount = max(0, total_cost - discount)

            # Check if "Add VAT" is True in the cart
            if user_cart.add_vat:
                vat_rate = Decimal('0.16')  # 16% VAT rate
                vat = round(total_cost_after_discount * vat_rate)
                total_payable = total_cost_after_discount + vat
            else:
                vat = 0
                total_payable = total_cost_after_discount

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
        filtered_buyers = buyers.filter(Q(first_name__icontains=buyer_name_or_phone) | Q(
            last_name__icontains=buyer_name_or_phone) | Q(phone_number__icontains=buyer_name_or_phone))

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

    payment_methods = PaymentMethod.objects.all()

    context = {
        'carts': user_cart,
        'cart': cart_items,
        'total': total_cost,
        'products': products,
        'categories': categories,
        'buyers': buyers,
        'payment_methods': payment_methods,
        'discount': discount,
        'vat': vat,
        'total_payable': total_payable,
    }

    return render(request, 'pos/index.html', context)


@login_required
@third
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
@third
def add_to_cart(request, product_id, quantity=1):
    # Retrieve the product based on the product_id or handle errors if it doesn't exist
    product = get_object_or_404(Product, pk=product_id)

    # Check if the product is out of stock
    if product.quantity <= 0:
        # Handle the case where the product is out of stock
        messages.error(request, 'This product is out of stock.')
        # Redirect to the product list page or another appropriate URL
        return redirect('pos:index')

    # Retrieve or create the user's cart using the custom user model
    User = get_user_model()  # Get the custom user model
    # Assuming the user is authenticated
    user = User.objects.get(username=request.user.username)
    cart, created = Cart.objects.get_or_create(user=user)

    # Retrieve the cart item for the product or create it if it doesn't exist
    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)

    # Check if adding the specified quantity exceeds the available quantity
    if cart_item.quantity is not None and cart_item.quantity + quantity > product.quantity:
        # Handle the case where there isn't enough quantity available
        messages.error(
            request, 'There is not enough quantity available for this product.')
        # Redirect to the product list page or another appropriate URL
        return redirect('pos:index')

    # If there is enough quantity available, update the cart
    if cart_item.quantity is not None:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    # Redirect to the cart or another appropriate URL
    return redirect('pos:index')  # Replace 'cart' with your cart URL name


@login_required
@third
def cart(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Retrieve the user's cart
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Calculate the total cost of items in the cart
            total_cost = user_cart.cartitem_set.aggregate(total_cost=Sum(
                models.F('product__price') * models.F('quantity')))['total_cost'] or 0.0

            discount = Decimal(request.POST.get('discount', '0.0'))

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


@login_required
@third
def update_discount(request):
    if request.method == 'POST':
        # Retrieve the user's cart
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            # Get the new discount value from the form
            new_discount_str = request.POST.get('new_discount', '0.0')

            if new_discount_str and new_discount_str.replace('.', '', 1).isdigit():
                # Convert the new discount to a Decimal
                new_discount = Decimal(new_discount_str)

                # Update the discount in the cart
                user_cart.discount = new_discount
                user_cart.save()

                # Redirect back to the cart or another relevant page
                return redirect('pos:index')
            else:
                # Show a message if the input is not a valid decimal
                messages.error(
                    request, 'Please provide a valid discount value.')

    # Handle GET requests (display the form to update the discount)
    return render(request, 'pos/index.html')


@login_required
@third
def increment_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    # Check if incrementing the quantity exceeds the product's available quantity
    if cart_item.quantity < cart_item.product.quantity:
        cart_item.quantity += 1
        cart_item.save()
    else:
        # If incrementing is not allowed, show an error message
        messages.error(
            request, "Cannot increase quantity beyond available quantity.")

    return redirect('pos:index')


@login_required
@third
def decrement_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    # Check if the quantity is greater than 1 before decrementing
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()

    return redirect('pos:index')


@login_required
@third
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('pos:index')


@login_required
@third
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

    # Calculate the x-position for left-aligned text with a small padding
    x_left_aligned = 20

    # Create the PDF object with custom page size (width x height)
    p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Add a logo to the header
    logo_path = 'https://healthtoday.co.ke/wp-content/uploads/2023/03/cropped-Logo-232x77.png'
    logo_width = 100  # Adjust the width of the logo
    logo_height = 50  # Adjust the height of the logo
    x_centered_logo = (page_width - logo_width) / 2
    p.drawInlineImage(logo_path, x_centered_logo, page_height -
                      20 - logo_height, width=logo_width, height=logo_height)

    # Set the font and font size for the shop details
    p.setFont("Helvetica", 10)

    # Define the content for shop address, sale date, PIN, and sale ID (customize as needed)
    shop_address = "St Ellis Building, City Hall Way, Nairobi"
    contact = "+254794085329 | info@healthtoday.co.ke "
    sale_date = sale.sale_date.strftime("Date: %Y-%m-%d %H:%M:%S")
    shop_pin = "Shop PIN: P0513834130"
    sale_id = f"CASH SALE: {sale.id:04d}"

    # Calculate the y-positions for other content
    address_y_position = page_height - 100
    contact_y_position = address_y_position - 15
    date_y_position = contact_y_position - 15
    pin_y_position = date_y_position - 15
    sale_id_y_position = pin_y_position - 15

    # Draw the shop details aligned to the left with padding
    draw_left_aligned_text(p, shop_address, x_left_aligned,
                           address_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, contact, x_left_aligned,
                           contact_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, sale_date, x_left_aligned,
                           date_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, shop_pin, x_left_aligned,
                           pin_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, sale_id, x_left_aligned,
                           sale_id_y_position, "Helvetica", 10)

    # Draw double-dotted lines below the details
    dotted_line_y_position = sale_id_y_position - 10
    p.setDash(3, 3)  # Set the dash pattern for the lines
    p.line(x_left_aligned, dotted_line_y_position,
           x_left_aligned + receipt_width, dotted_line_y_position)

    # Set the font and font size for sales details headers
    p.setFont("Helvetica", 10)  # No longer bold

    # headers
    sales_details = [
        ["Item", "Price", "Amount"]
    ]

    # data
    for sale_item in SaleItem.objects.filter(sale=sale):
        product_name = sale_item.product.title
        unit_price = sale_item.unit_price
        quantity = sale_item.quantity_sold
        total_price = sale_item.quantity_sold * unit_price

        # Add the item, price, and the total amount to the detail
        detail = [product_name, "", ""]

        sales_details.append(detail)

        # Add the "1 x 300.00" line below the item
        detail_quantity = [f"{quantity} x",
                           f"{unit_price:.2f}", f"{total_price:.2f}"]
        sales_details.append(detail_quantity)

    # Calculate the y-position for sales details
    sales_details_y_position = dotted_line_y_position - 25

    # Create the table without grid lines
    table = Table(sales_details, colWidths=[90, 40, 50], rowHeights=15)
    table.setStyle(TableStyle([
        # Add left padding to align contents to the left
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Align text to the left
        # Text color for the first row (headers)
        ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
    ]))

    # Calculate the position to align the table to the left
    table_x_position = x_left_aligned

    # Calculate the total height of the table
    table_height = len(sales_details) * 15  # Assuming row height is 15

    # Adjust the position to ensure it doesn't go beyond the page
    if sales_details_y_position - table_height < 0:
        sales_details_y_position = table_height

    # Draw the table aligned to the left
    table.wrapOn(p, page_width, page_height)
    table.drawOn(p, table_x_position, sales_details_y_position - table_height)

    # Calculate positions for "Total VAT," "Total Payable," and "Total Paid"
    total_vat_y_position = sales_details_y_position - table_height - 25
    total_payable_y_position = total_vat_y_position - 15
    discount_y_position = total_payable_y_position - 15
    total_paid_y_position = discount_y_position - 15

    # Add text for "Total VAT," "Total Payable," and "Total Paid" from the Sale model
    total_vat_text = f"VAT: {sale.vat:.2f}"
    total_payable_text = f"Total: {sale.total_amount:.2f}"
    discount_text = f"Discount: {sale.discount:.2f}"
    total_paid_text = f"Total Paid: {sale.total_paid:.2f}"

    draw_left_aligned_text(p, total_vat_text, x_left_aligned,
                           total_vat_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, total_payable_text, x_left_aligned,
                           total_payable_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, discount_text, x_left_aligned,
                           discount_y_position, "Helvetica", 10)
    draw_left_aligned_text(p, total_paid_text, x_left_aligned,
                           total_paid_y_position, "Helvetica", 10)

    # Draw double-dotted lines below the totals
    p.setDash(3, 3)  # Set the dash pattern for the lines
    p.line(x_left_aligned, total_paid_y_position - 10,
           x_left_aligned + receipt_width, total_paid_y_position - 10)

    # Add a line for "You were served by"
    served_by_y_position = total_paid_y_position - 20
    draw_left_aligned_text(
        p, f"You were served by: {served_by_username}", x_left_aligned, served_by_y_position, "Helvetica", 10)

    # Generate a barcode for the sale ID
    formatted_sale_id = f"{sale.id:04d}"

    # Generate a barcode image using the formatted sale ID
    barcode_image = generateBarcodeImage(formatted_sale_id)

    # Calculate the x-position for centering the barcode within the receipt width
    barcode_width = 100  # Adjust the width as needed
    barcode_x_position = x_centered + (receipt_width - barcode_width) / 2
    barcode_y_position = served_by_y_position - 60  # Adjust as needed

    # Draw the barcode on the PDF
    p.drawImage(barcode_image, barcode_x_position,
                barcode_y_position, width=barcode_width, height=50)

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

  # Reset the buffer for reading
    buffer.seek(0)

    # Create a response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="receipt.pdf"'

    return response


# Function to draw left-aligned text
def draw_left_aligned_text(pdf_canvas, text, x_position, y_position, font_name, font_size):
    pdf_canvas.setFont(font_name, font_size)
    pdf_canvas.drawString(x_position, y_position, text)


def generateBarcodeImage(data):
    # Generate a barcode image using the Python barcode library
    barcode = generate('Code128', str(
        data), writer=ImageWriter(), output='barcode_image')
    return barcode


@login_required
@third
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
                discount=user_cart.discount,
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
            user_cart.discount = 0
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
            return pdf_data

        else:
            messages.warning(
                request, 'Your cart is empty. Please add items to your cart before checking out.')

    except Exception as e:
        messages.error(request, f'An error occurred during checkout: {str(e)}')

    return redirect('pos:cart')


@login_required
@third
def sales(request):
    # Get the current datetime with timezone information
    current_datetime = timezone.now()

    # Get the current date without the time portion
    current_date = current_datetime.date()
    print(current_date)

    # Calculate the start and end of the current day
    start_of_day = timezone.make_aware(timezone.datetime(
        current_date.year, current_date.month, current_date.day, 0, 0, 0))
    end_of_day = timezone.make_aware(timezone.datetime(
        current_date.year, current_date.month, current_date.day, 23, 59, 59))

    # Retrieve a list of sales records for the current date
    sales = Sale.objects.filter(sale_date__range=(
        start_of_day, end_of_day)).order_by('-sale_date')

    # Calculate total sales amount for the current date
    total_sales_amount = sales.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0

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
    sales_data_json = json.dumps(
        {'sale_ids': sale_ids, 'total_amounts': total_amounts})
    print(sales_data_json)

    context = {
        'sales': page,
        'total_sales_amount': total_sales_amount,
        'sales_data_json': sales_data_json,
        'date': current_date
    }

    return render(request, 'pos/sales.html', context)


@login_required
@third
def sale(request, sale_id):
    # Retrieve the sale object for the given sale_id or return a 404 if not found
    sale = get_object_or_404(Sale, id=sale_id)

    # Now, you can access the related SaleItems for this sale using sale.saleitem_set.all()
    sale_items = sale.saleitem_set.all()

    current_datetime = timezone.now()

    # Get the current date without the time portion
    current_date = current_datetime.date()

    # Calculate the start and end of the current day
    start_of_day = timezone.make_aware(timezone.datetime(
        current_date.year, current_date.month, current_date.day, 0, 0, 0))
    end_of_day = timezone.make_aware(timezone.datetime(
        current_date.year, current_date.month, current_date.day, 23, 59, 59))

    # Retrieve a list of sales records for the current date
    sales = Sale.objects.filter(sale_date__range=(
        start_of_day, end_of_day)).order_by('-sale_date')

    # Calculate total sales amount for the current date
    total_sales_amount = sales.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0

    # Create a Paginator object with 10 items per page
    paginator = Paginator(sales, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page number
    page = paginator.get_page(page_number)

    # Prepare data for a bar chart displaying total sales amounts for the current date
    sale_ids = [sale.id for sale in sales]
    total_amounts = [float(sale.total_amount)
                     for sale in sales]  # Convert Decimal to float

    # Prepare data for a chart displaying sold items
    sold_item_labels = [item.product.title for item in sale_items]
    sold_item_quantities = [item.quantity_sold for item in sale_items]

    # Convert the data to JSON format for use in JavaScript
    sales_data_json = json.dumps(
        {'sale_ids': sale_ids, 'total_amounts': total_amounts})
    sold_items_data_json = json.dumps(
        {'labels': sold_item_labels, 'quantities': sold_item_quantities})

    context = {
        'sale': sale,
        'date': current_date,
        'today_sales': sale_items,
        'sales': page,
        'total_sales_amount': total_sales_amount,
        'sales_data_json': sales_data_json,  # Pass the total sales data to the template
        # Pass the sold items data to the template
        'sold_items_data_json': sold_items_data_json,
    }

    return render(request, 'pos/sales.html', context)


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


@login_required
@third
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
            end_date = datetime.strptime(
                end_date_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

            # Convert the start and end dates to the timezone used in the Sale model
            start_date = timezone.make_aware(
                start_date, timezone.get_current_timezone())
            end_date = timezone.make_aware(
                end_date, timezone.get_current_timezone())

            # Filter sales within the specified date range
            sales_data = sales_data.filter(
                sale_date__range=(start_date, end_date))
        except ValueError:
            # Handle invalid date format
            messages.warning(
                request, 'Invalid date format. Please use YYYY-MM-DD format.')

    # Calculate the total amounts
    total_sales_amount = sales_data.aggregate(total_sales=Sum('total_amount'))[
        'total_sales'] or Decimal('0.0')
    total_vat_amount = sales_data.aggregate(total_vat=Sum('vat'))[
        'total_vat'] or Decimal('0.0')
    total_paid_amount = sales_data.aggregate(total_paid=Sum('total_paid'))[
        'total_paid'] or Decimal('0.0')

    # Get sold items for each sale
    sold_items = SaleItem.objects.filter(sale__in=sales_data)

    # Aggregate total quantity sold for each product
    product_sales = sold_items.values('product__title', 'product__category__name').annotate(
        total_quantity_sold=Sum('quantity_sold')
    )

    # Calculate total sales amount for each category
    category_sales = sold_items.values('product__category__name').annotate(
        total_category_sales=Sum(
            F('quantity_sold') * F('unit_price'), output_field=DecimalField())
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
        's_date': start_date_param,
        'e_date': end_date_param
    }

    return render(request, 'pos/sales_h.html', context)


@login_required
@third
def menu(request):
    return render(request, 'pos/menu.html')


@login_required
@third
def expiring(request):
    # Get the current date
    current_date = timezone.now().date()

    # Retrieve expired products and products that are 5 days from expiry
    expired_products = Product.objects.filter(expiry_date__lt=current_date)
    print(expired_products)
    expiring_soon_products = Product.objects.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=current_date + timezone.timedelta(days=5)
    )

    print(expiring_soon_products)

    context = {
        'expired': expired_products,
        'expiring_soon': expiring_soon_products
    }

    return render(request, 'pos/expiring.html', context)


@login_required
@third
def receivings(request):
    receivings_list = Receiving.objects.all()
    return render(request, 'pos/receivings.html', {'receivings_list': receivings_list})


@login_required
@third
def supplies(request):
    supplies_list = Supply.objects.all()
    return render(request, 'pos/supplies.html', {'supplies_list': supplies_list})


@login_required
@third
def about(request):
    about = About.objects.all()
    return render(request, 'pos/about.html', {'about': about})


@login_required
@third
def cataloque(request):
    cataloque = Category.objects.annotate(total_products=Count('product'))
    context = {
        'cat': cataloque
    }
    return render(request, 'pos/cataloque.html', context)


def cataloque_detail(request, cataloque_id):
    category = get_object_or_404(Category, pk=cataloque_id)
    products_in_category = Product.objects.filter(category=category)

    context = {
        'cat': category,
        'products': products_in_category,

    }

    return render(request, 'pos/cataloque_detail.html', context)


def export_cataloque(request, cataloque_id):
    # Get category and products in the category
    category = get_object_or_404(Category, pk=cataloque_id)
    products_in_category = Product.objects.filter(category=category)

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{category.name}_products.pdf"'

    # Create PDF document with letter size
    p = SimpleDocTemplate(response, pagesize=letter)

    # Add custom header and footer
    header_text = "Health Today Products"
    category_text = f"{category.name}"
    footer_text = "+254794085329 \n | \n info@healthtoday.co.ke | St Ellis Building, City Hall Way, Nairobi, Kenya"

    # Add table headers
    headers = ['#', 'Product', 'Category', 'Brand', 'Units', 'Price']
    col_widths = [30, 200, 110, 100, 50, 50]

    # Create table data
    table_data = [headers]
    for index, product in enumerate(products_in_category):
        row = [str(index + 1), product.title, product.category.name,
               str(product.brand), str(product.units), str(product.price)]
        table_data.append(row)

    # Create table and set styles
    table = Table(table_data, colWidths=col_widths)
    style = TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    table.setStyle(style)

    # Create header and footer paragraphs with centered alignment
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        alignment=1  # 0=left, 1=center, 2=right
    )
    header = Paragraph(header_text, header_style)

    category_paragraph_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        alignment=1  # 0=left, 1=center, 2=right
    )
    category_paragraph = Paragraph(category_text, category_paragraph_style)

    footer_style = styles["BodyText"]
    footer = Paragraph(footer_text, footer_style)

    # Add a logo to the header
    logo_path = 'https://healthtoday.co.ke/wp-content/uploads/2023/03/cropped-Logo-232x77.png'
    logo = Image(logo_path, width=2*inch, height=1*inch)

    # Build the PDF document with header, logo, and footer
    story = [logo, header, category_paragraph, table, footer]
    p.build(story)

    return response
