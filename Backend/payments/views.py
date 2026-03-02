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
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order

from .models import Payment, PaymentWebhookEvent

logger = logging.getLogger(__name__)


class RazorpayIntegrationError(Exception):
    pass


def _compute_signature(message: str, secret: str) -> str:
    return hmac.new(secret.encode(), msg=message.encode(), digestmod=hashlib.sha256).hexdigest()


def _payment_entity(payload: dict) -> dict:
    return (((payload.get("payload") or {}).get("payment") or {}).get("entity") or {})


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
                return Response({"detail": "Order already paid."}, status=status.HTTP_409_CONFLICT)
            duplicate = Payment.objects.filter(razorpay_payment_id=razorpay_payment_id).exclude(id=payment.id).exists()
            if duplicate:
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
                payment.order.payment_status = Order.PaymentStatus.FAILED
                payment.order.save(update_fields=["payment_status", "updated_at"])
                logger.warning("Payment signature verification failed for order_id=%s", payment.order_id)
                return Response({"detail": "Invalid payment signature."}, status=status.HTTP_400_BAD_REQUEST)

            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = Payment.Status.CAPTURED
            payment.verified_at = timezone.now()
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
            payment.order.save(update_fields=["payment_status", "updated_at"])

        return Response({"detail": "Payment verified successfully."}, status=status.HTTP_200_OK)


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
            if event_type == "payment.captured":
                payment.status = Payment.Status.CAPTURED
                payment.verified_at = timezone.now()
                payment.order.payment_status = Order.PaymentStatus.PAID
                payment.order.save(update_fields=["payment_status", "updated_at"])
            elif event_type == "payment.failed":
                payment.status = Payment.Status.FAILED
                payment.failure_reason = entity.get("error_description", "")
                payment.order.payment_status = Order.PaymentStatus.FAILED
                payment.order.save(update_fields=["payment_status", "updated_at"])
                logger.error("Payment failed via webhook for order_id=%s", payment.order_id)
            elif event_type == "payment.authorized":
                payment.status = Payment.Status.AUTHORIZED
            payment.save()

        return Response({"detail": "Webhook processed."}, status=status.HTTP_200_OK)
