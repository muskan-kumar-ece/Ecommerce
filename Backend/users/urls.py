from django.urls import path

from .views import CurrentUserView, ReferralSummaryView, RegisterUserView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="user-register"),
    path("referral-summary/", ReferralSummaryView.as_view(), name="referral-summary"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
