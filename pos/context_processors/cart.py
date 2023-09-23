from product.models import CartItem

def cart_items(request):
    cart_item_count = 0  # Initialize the count to zero
    cart_items = []  # Initialize an empty list for cart items
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        # Calculate the total count by summing up the quantities of all cart items
        cart_item_count = sum(cart_item.quantity for cart_item in cart_items)
    return {'count': cart_item_count, 'cart_items': cart_items}
