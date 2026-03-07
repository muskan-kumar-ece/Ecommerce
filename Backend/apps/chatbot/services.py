import json
import logging
import re
from urllib import error, request

from django.conf import settings

from apps.recommendations.services import get_user_recommendations
from orders.models import Order

logger = logging.getLogger(__name__)

ORDER_ID_PATTERN = re.compile(r"(?:order(?:\s+id)?\s*[#:]?\s*)(\d+)", re.IGNORECASE)


def extract_order_id(message):
    match = ORDER_ID_PATTERN.search(message or "")
    if not match:
        return None
    return int(match.group(1))


def _get_order_context(user, message):
    order_id = extract_order_id(message)
    queryset = (
        Order.objects.filter(user=user)
        .prefetch_related("shipping_events")
        .only("id", "status", "payment_status", "tracking_id", "updated_at")
    )
    if order_id is not None:
        order = queryset.filter(id=order_id).first()
    else:
        order = queryset.order_by("-created_at").first()
    return order, order_id


def _format_order_details(order):
    if order is None:
        return None
    return {
        "order_id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "tracking_id": order.tracking_id,
        "last_updated_at": order.updated_at.isoformat(),
    }


def _format_suggestions(products):
    return [
        {
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "category": product.category.name,
        }
        for product in products[:3]
    ]


def _build_fallback_response(intent, order, requested_order_id, suggestions):
    if intent == "order_status":
        if order is None:
            if requested_order_id is not None:
                return f"I couldn't find order #{requested_order_id} in your account."
            return "I couldn't find any orders in your account yet."
        tracking_text = f" Tracking ID: {order.tracking_id}." if order.tracking_id else ""
        return (
            f"Your order #{order.id} is currently {order.status.replace('_', ' ')}. "
            f"Payment status is {order.payment_status.replace('_', ' ')}.{tracking_text}"
        )

    if intent == "refund":
        if order is None:
            return (
                "For refunds, please share your order ID and we can check eligibility. "
                "Refunds are usually processed to the original payment method after approval."
            )
        if order.status == Order.Status.REFUNDED or order.payment_status == Order.PaymentStatus.REFUNDED:
            return f"Order #{order.id} is already refunded."
        return (
            f"Refund request for order #{order.id} can be initiated if eligible. "
            f"Current order status is {order.status.replace('_', ' ')}."
        )

    if intent == "product_suggestions":
        if not suggestions:
            return "I can suggest products after we gather a little more shopping history."
        first = suggestions[0]["name"]
        return f"Based on your activity, you might like {first} and similar products."

    return "I can help with order status, refund queries, and product suggestions."


def _call_openai_response(user_message, intent, order_details, suggestions):
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return None

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    context = {
        "intent": intent,
        "order_details": order_details,
        "suggestions": suggestions,
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise ecommerce support assistant. "
                    "Use provided context for accurate order/refund answers and product suggestions."
                ),
            },
            {"role": "user", "content": f"User message: {user_message}\nContext: {json.dumps(context)}"},
        ],
        "temperature": 0.3,
    }
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
        logger.warning("OpenAI chatbot request failed: %s", exc)
        return None

    choices = data.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    return None


def build_chatbot_response(user, message):
    normalized_message = message.lower()
    intent = "general"
    order = None
    requested_order_id = None
    suggestions = []

    if "order status" in normalized_message:
        intent = "order_status"
        order, requested_order_id = _get_order_context(user, message)
    elif "refund" in normalized_message:
        intent = "refund"
        order, requested_order_id = _get_order_context(user, message)
    elif "suggest products" in normalized_message or "recommend" in normalized_message:
        intent = "product_suggestions"
        suggestions = _format_suggestions(get_user_recommendations(user.id))

    order_details = _format_order_details(order)
    ai_response = _call_openai_response(message, intent, order_details, suggestions)
    fallback_response = _build_fallback_response(intent, order, requested_order_id, suggestions)

    return {
        "intent": intent,
        "response": ai_response or fallback_response,
        "order_details": order_details,
        "suggestions": suggestions,
    }
