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

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
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

    user_cart = Cart.objects.filter(user=request.user).first()

    if user_cart:
        # Calculate the total cost of items in the cart
        total_cost = user_cart.cartitem_set.aggregate(total_cost=Sum(models.F('product__price') * models.F('quantity')))['total_cost'] or 0.0

        # Update the total_cost field in the Cart model
        user_cart.total_cost = total_cost
        user_cart.save()

        # Retrieve the cart items associated with the cart
        cart_items = user_cart.cartitem_set.all()

    # Paginate the products with 6 products per page
    paginator = Paginator(products, 24)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results
        products = paginator.page(paginator.num_pages)

    context = {
        'cart': cart_items,
        'total': user_cart.total_cost,
        'products': products,
        'categories': categories,
    }

    return render(request, 'pos/index.html', context)



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
    cart_item.quantity += 1
    cart_item.save()
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

@login_required
def checkout(request):
    # Retrieve the user's cart
    user_cart = get_object_or_404(Cart, user=request.user)

    # Check if the cart is not empty
    if user_cart.products.exists():
        try:
            # Create a new sale
            sale = Sale.objects.create(user=request.user, total_amount=user_cart.total_cost)

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
            print(today)

            current_day = Day.objects.get(week__month__year__year=sale_date.year,
                                          week__month__month=sale_date.month,
                                          week__week_number=sale_date.isocalendar()[1],
                                          day_of_week=today)
            current_day.sales.add(sale)
            current_day.sales_amount += sale.total_amount
            current_day.save()

            # Update the Week model for the current week
            current_week = current_day.week
            current_week.sales_amount += sale.total_amount
            current_week.save()

            # Update the Month model for the current month
            current_month = current_week.month
            current_month.sales_amount += sale.total_amount
            current_month.save()

            # Update the Year model for the current year
            current_year = current_month.year
            current_year.sales_amount += sale.total_amount
            current_year.save()

            messages.success(request, 'Checkout successful. Your order has been placed.')
        except Exception as e:
            messages.error(request, f'An error occurred during checkout: {str(e)}')
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
