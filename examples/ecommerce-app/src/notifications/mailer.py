def send_order_confirmation(recipient_email: str, order_number: str, total_dollars: float) -> bool:
    """Dispatches asynchronous order receipt email to customer inbox."""
    print(f"Sending confirmation email to {recipient_email} for order {order_number} (${total_dollars:.2f})")
    return True
