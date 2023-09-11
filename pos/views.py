from django.shortcuts import render
from product.models import Product, Category  # Import the Category model

def index(request):
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

    return render(request, 'pos/index.html', {'products': products, 'categories': categories})
