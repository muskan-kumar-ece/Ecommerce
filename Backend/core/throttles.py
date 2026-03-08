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
