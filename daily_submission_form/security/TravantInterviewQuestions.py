# order_lines = [
#     {"product_name": "Laptop", "quantity": 2, "unit_price": 50000, "discount_percent": 10},
#     {"product_name": "Mouse", "quantity": 3, "unit_price": 1000, "discount_percent": 5}
# ]chat

# You are given a list of sale order lines.
# Each line contains:
# product_name (string)
# quantity (integer)
# unit_price (float)
# discount_percent (float)
# Tax is 18% on the discounted price.

# Write a Python function:
# The function should:
# Calculate line subtotal = quantity × unit_price
# Apply discount
# Apply 18% tax on discounted amount
# Return final order total rounded to 2 decimals


def calculate_order_total(quantity, unit_price, discount_percent):
    """
    Calculate final order total.
    
    Parameters:
    quantity (int or float): Number of items
    unit_price (float): Price per item
    discount_percent (float): Discount percentage (e.g., 10 for 10%)
    
    Returns:
    float: Final total rounded to 2 decimals
    """
    
    # Step 1: Line subtotal
    subtotal = quantity * unit_price
    
    # Step 2: Apply discount
    discount_amount = subtotal * (discount_percent / 100)
    discounted_total = subtotal - discount_amount
    
    # Step 3: Apply 18% tax
    tax = discounted_total * 0.18
    final_total = discounted_total + tax
    
    # Step 4: Round to 2 decimals
    return round(final_total, 2)
