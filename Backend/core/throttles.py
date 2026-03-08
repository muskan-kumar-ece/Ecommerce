from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthTokenThrottle(AnonRateThrottle):
    scope = "auth"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class OrderCreateRateThrottle(UserRateThrottle):
    scope = "order_create"


class PaymentRateThrottle(UserRateThrottle):
    scope = "payments"


class AdminRateThrottle(UserRateThrottle):
    scope = "admin"


class ReviewRateThrottle(UserRateThrottle):
    scope = "reviews"


class ChatbotRateThrottle(UserRateThrottle):
    scope = "chatbot"


class WebhookRateThrottle(AnonRateThrottle):
    scope = "payments_webhook"


class WishlistMutationRateThrottle(UserRateThrottle):
    scope = "wishlist_mutations"


class PriceWatchRateThrottle(UserRateThrottle):
    scope = "price_watch"
