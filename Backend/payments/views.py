import base64
import hashlib
import hmac
import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from products.models import Product

from .models import Payment, PaymentEvent, PaymentWebhookEvent

logger = logging.getLogger(__name__)


class RazorpayIntegrationError(Exception):
    pass


def _compute_signature(message: str, secret: str) -> str:
    return hmac.new(secret.encode(), msg=message.encode(), digestmod=hashlib.sha256).hexdigest()


def _payment_entity(payload: dict) -> dict:
    return (((payload.get("payload") or {}).get("payment") or {}).get("entity") or {})


def _deduct_order_stock(order: Order) -> None:
    if order.stock_deducted:
        return

    order_items = list(order.items.all())
    if not order_items:
        order.stock_deducted = True
        order.save(update_fields=["stock_deducted", "updated_at"])
        return

    product_ids = [item.product_id for item in order_items]
    list(Product.objects.select_for_update().filter(id__in=product_ids))
    for item in order_items:
        updated = Product.objects.filter(id=item.product_id, stock_quantity__gte=item.quantity).update(
            stock_quantity=F("stock_quantity") - item.quantity
        )
        if not updated:
            raise ValidationError({"detail": "Insufficient stock for one or more items."})

    order.stock_deducted = True
    order.save(update_fields=["stock_deducted", "updated_at"])


def _create_razorpay_order(amount: int, currency: str, receipt: str) -> dict:
    payload = json.dumps(
        {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1,
        }
    ).encode()
    credentials = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    request = Request(
        f"{settings.RAZORPAY_API_BASE_URL.rstrip('/')}/orders",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64.b64encode(credentials).decode()}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RazorpayIntegrationError("Failed to create Razorpay order") from exc


class CreateRazorpayOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.error(
                "Razorpay key configuration is missing: key_id=%s key_secret=%s",
                bool(settings.RAZORPAY_KEY_ID),
                bool(settings.RAZORPAY_KEY_SECRET),
            )
            return Response({"detail": "Payment gateway configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order_id = request.data.get("order_id")
        idempotency_key = request.META.get("HTTP_IDEMPOTENCY_KEY") or request.data.get("idempotency_key")
        if not order_id or not idempotency_key:
            return Response(
                {"detail": "order_id and idempotency_key are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                order = (
                    Order.objects.select_for_update()
                    .filter(id=order_id, user=request.user)
                    .first()
                )
                if not order:
                    return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
                if order.payment_status == Order.PaymentStatus.PAID:
                    return Response({"detail": "Order already paid."}, status=status.HTTP_409_CONFLICT)

                existing_payment = Payment.objects.filter(idempotency_key=idempotency_key).first()
                if existing_payment:
                    if existing_payment.order_id != order.id:
                        return Response({"detail": "Idempotency key is already used."}, status=status.HTTP_409_CONFLICT)
                    return Response(
                        {
                            "payment_id": existing_payment.id,
                            "razorpay_order_id": existing_payment.razorpay_order_id,
                            "amount": existing_payment.amount,
                            "currency": existing_payment.currency,
                            "key_id": settings.RAZORPAY_KEY_ID,
                        },
                        status=status.HTTP_200_OK,
                    )

                amount_paise = int((Decimal(order.total_amount) * Decimal("100")).quantize(Decimal("1")))
                razorpay_order = _create_razorpay_order(
                    amount=amount_paise,
                    currency="INR",
                    receipt=f"order_{order.id}",
                )

                payment = Payment.objects.create(
                    order=order,
                    idempotency_key=idempotency_key,
                    razorpay_order_id=razorpay_order["id"],
                    amount=razorpay_order.get("amount", amount_paise),
                    currency=razorpay_order.get("currency", "INR"),
                    status=razorpay_order.get("status", Payment.Status.CREATED),
                    raw_response=razorpay_order,
                )
        except (RazorpayIntegrationError, KeyError, InvalidOperation):
            logger.exception("Order creation failed")
            return Response({"detail": "Unable to create payment order."}, status=status.HTTP_502_BAD_GATEWAY)
        except IntegrityError:
            return Response({"detail": "Duplicate payment attempt detected."}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                "payment_id": payment.id,
                "razorpay_order_id": payment.razorpay_order_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "key_id": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyRazorpayPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return Response({"detail": "Missing payment verification fields."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = (
                Payment.objects.select_for_update()
                .select_related("order")
                .filter(razorpay_order_id=razorpay_order_id, order__user=request.user)
                .first()
            )
            if not payment:
                return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
            if payment.order.payment_status == Order.PaymentStatus.PAID:
                PaymentEvent.objects.create(
                    payment=payment,
                    event_type=PaymentEvent.EventType.REPLAY,
                    metadata={"reason": "already_paid"},
                )
                return Response({"detail": "Payment already verified."}, status=status.HTTP_200_OK)
            duplicate = Payment.objects.filter(razorpay_payment_id=razorpay_payment_id).exclude(id=payment.id).exists()
            if duplicate:
                PaymentEvent.objects.create(
                    payment=payment,
                    event_type=PaymentEvent.EventType.DUPLICATE,
                    metadata={"razorpay_payment_id": razorpay_payment_id},
                )
                logger.warning("Duplicate Razorpay payment id received: %s", razorpay_payment_id)
                return Response({"detail": "Duplicate payment id."}, status=status.HTTP_409_CONFLICT)

            expected_signature = _compute_signature(
                f"{razorpay_order_id}|{razorpay_payment_id}",
                settings.RAZORPAY_KEY_SECRET,
            )
            if not hmac.compare_digest(expected_signature, razorpay_signature):
                payment.status = Payment.Status.FAILED
                payment.failure_reason = "Invalid signature"
                payment.save(update_fields=["status", "failure_reason", "updated_at"])
                PaymentEvent.objects.create(
                    payment=payment,
                    event_type=PaymentEvent.EventType.FAILED,
                    metadata={"reason": "invalid_signature"},
                )
                payment.order.payment_status = Order.PaymentStatus.FAILED
                payment.order.save(update_fields=["payment_status", "updated_at"])
                logger.warning("Payment signature verification failed for order_id=%s", payment.order_id)
                return Response({"detail": "Invalid payment signature."}, status=status.HTTP_400_BAD_REQUEST)

            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = Payment.Status.CAPTURED
            payment.verified_at = timezone.now()
            if (
                payment.order.payment_status != Order.PaymentStatus.PAID
                and not payment.order.stock_deducted
            ):
                _deduct_order_stock(payment.order)
            payment.save(
                update_fields=[
                    "razorpay_payment_id",
                    "razorpay_signature",
                    "status",
                    "verified_at",
                    "updated_at",
                ]
            )
            payment.order.payment_status = Order.PaymentStatus.PAID
            order_update_fields = ["payment_status", "updated_at"]
            if payment.order.status != Order.Status.CONFIRMED:
                payment.order.status = Order.Status.CONFIRMED
                order_update_fields.append("status")
            payment.order.save(update_fields=order_update_fields)
            PaymentEvent.objects.create(
                payment=payment,
                event_type=PaymentEvent.EventType.VERIFIED,
                metadata={"razorpay_payment_id": razorpay_payment_id},
            )

        return Response({"detail": "Payment verified successfully."}, status=status.HTTP_200_OK)


class RefundOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.select_for_update().filter(id=order_id, user=request.user).first()
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if order.payment_status == Order.PaymentStatus.REFUNDED:
            if order.status != Order.Status.REFUNDED:
                order.status = Order.Status.REFUNDED
                order.save(update_fields=["status", "updated_at"])
            payment = Payment.objects.filter(order=order).order_by("-created_at").first()
            if payment:
                PaymentEvent.objects.create(
                    payment=payment,
                    event_type=PaymentEvent.EventType.REPLAY,
                    metadata={"reason": "already_refunded"},
                )
            return Response({"detail": "Order already refunded."}, status=status.HTTP_200_OK)
        if order.payment_status != Order.PaymentStatus.PAID:
            return Response({"detail": "Only paid orders can be refunded."}, status=status.HTTP_400_BAD_REQUEST)

        payment = (
            Payment.objects.select_for_update()
            .filter(order=order, status=Payment.Status.CAPTURED)
            .order_by("-created_at")
            .first()
        )
        if not payment:
            return Response({"detail": "Captured payment not found for this order."}, status=status.HTTP_400_BAD_REQUEST)

        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        PaymentEvent.objects.create(
            payment=payment,
            event_type=PaymentEvent.EventType.REFUNDED,
            metadata={"order_id": order.id},
        )
        order.payment_status = Order.PaymentStatus.REFUNDED
        order.status = Order.Status.REFUNDED
        order.save(update_fields=["payment_status", "status", "updated_at"])
        return Response({"detail": "Order refunded successfully."}, status=status.HTTP_200_OK)


class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.error("Razorpay webhook secret (RAZORPAY_WEBHOOK_SECRET) is not configured")
            return Response({"detail": "Webhook configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        raw_body = request.body
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not signature or not hmac.compare_digest(expected_signature, signature):
            logger.warning("Invalid Razorpay webhook signature")
            return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_400_BAD_REQUEST)

        event_id = request.META.get("HTTP_X_RAZORPAY_EVENT_ID") or hashlib.sha256(raw_body).hexdigest()
        event, created = PaymentWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={"event_type": request.data.get("event", "")},
        )
        if not created:
            return Response({"detail": "Webhook already processed."}, status=status.HTTP_200_OK)

        event_type = request.data.get("event")
        entity = _payment_entity(request.data)
        razorpay_order_id = entity.get("order_id")
        if not razorpay_order_id:
            return Response({"detail": "Webhook accepted."}, status=status.HTTP_200_OK)

        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related("order").filter(razorpay_order_id=razorpay_order_id).first()
            if not payment:
                logger.error("No payment found for webhook event_id=%s", event_id)
                return Response({"detail": "Webhook accepted."}, status=status.HTTP_200_OK)

            payment.razorpay_payment_id = entity.get("id") or payment.razorpay_payment_id
            payment.raw_response = request.data
            allowed_order_status_transitions = {
                Order.PaymentStatus.PENDING: {Order.PaymentStatus.PAID, Order.PaymentStatus.FAILED},
                Order.PaymentStatus.PAID: set(),
                Order.PaymentStatus.FAILED: set(),
            }
            if event_type == "payment.captured":
                current_status = payment.order.payment_status
                next_status = Order.PaymentStatus.PAID
                if next_status in allowed_order_status_transitions.get(current_status, set()):
                    _deduct_order_stock(payment.order)
                    payment.status = Payment.Status.CAPTURED
                    payment.verified_at = timezone.now()
                    payment.order.payment_status = next_status
                    payment.order.save(update_fields=["payment_status", "updated_at"])
                else:
                    logger.warning(
                        "Ignoring webhook transition %s -> %s for order_id=%s",
                        current_status,
                        next_status,
                        payment.order_id,
                    )
            elif event_type == "payment.failed":
                current_status = payment.order.payment_status
                next_status = Order.PaymentStatus.FAILED
                if next_status in allowed_order_status_transitions.get(current_status, set()):
                    payment.status = Payment.Status.FAILED
                    payment.failure_reason = entity.get("error_description", "")
                    payment.order.payment_status = next_status
                    payment.order.save(update_fields=["payment_status", "updated_at"])
                    logger.error("Payment failed via webhook for order_id=%s", payment.order_id)
                else:
                    logger.warning(
                        "Ignoring webhook transition %s -> %s for order_id=%s",
                        current_status,
                        next_status,
                        payment.order_id,
                    )
            elif event_type == "payment.authorized":
                payment.status = Payment.Status.AUTHORIZED
            payment.save()

        return Response({"detail": "Webhook processed."}, status=status.HTTP_200_OK)
