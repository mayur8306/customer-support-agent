import uuid
import pandas as pd

from backend.models import ConversationState


def tool_check_order(order_id: str) -> dict:
    """Queries the pandas DataFrame and returns raw data dictionary."""
    result = orders_db[orders_db['order_id'] == order_id.upper()]
    if not result.empty:
        return result.iloc[0].to_dict()
    return {"error": "not_found", "order_id": order_id}

def tool_escalate_to_zendesk(state: ConversationState) -> str:
    """Mocks an API call to a ticketing system."""
    state.is_escalated = True
    ticket_id = f"ZDK-{uuid.uuid4().hex[:6].upper()}"
    return f"Ticket {ticket_id} created. Transferring to a human agent."


orders_db = pd.DataFrame([
    {"order_id": "ORD1001", "item": "Wireless Mouse", "status": "Shipped", "eta": "2026-06-21"},
    {"order_id": "ORD1002", "item": "Bluetooth Earbuds", "status": "Processing", "eta": "2026-06-25"},
    {"order_id": "ORD1003", "item": "Mechanical Keyboard", "status": "Delivered", "eta": "2026-06-18"},
    {"order_id": "ORD1004", "item": "Gaming Monitor", "status": "Cancelled", "eta": "N/A"},
    {"order_id": "ORD1005", "item": "USB-C Hub", "status": "In Transit", "eta": "2026-06-20"}
])

knowledge_base = {
    "return_policy": "Our return policy allows items to be returned within 30 days of delivery in original packaging.",
    "warranty": "Electronics come with a standard 1-year manufacturer warranty covering hardware defects.",
    "shipping": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days.",
    "general_products": "We sell electronics including Wireless Mice, Earbuds, Keyboards, and Monitors."
}