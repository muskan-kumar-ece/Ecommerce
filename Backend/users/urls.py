from django.urls import path

from .views import ReferralSummaryView, RegisterUserView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="user-register"),
    path("referral-summary/", ReferralSummaryView.as_view(), name="referral-summary"),
]
