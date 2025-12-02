from dj_rest_auth.views import LogoutView, PasswordChangeView, UserDetailsView
from django.urls import path

from . import api_views

app_name = "authentication"

urlpatterns = [
    path("register/", api_views.RegisterViewWithAllowAny.as_view(), name="rest_register"),
    path("login/", api_views.LoginViewWith2fa.as_view(), name="rest_login"),
    path("verify-otp/", api_views.VerifyOTPView.as_view(), name="verify_otp"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path("password/change/", PasswordChangeView.as_view(), name="change_password"),
    path("token/verify/", api_views.TokenVerifyViewWithAllowAny.as_view(), name="token_verify"),
    path("token/refresh/", api_views.RefreshTokenViewWithAllowAny.as_view(), name="token_refresh"),
    path('api/token/', api_views.TokenObtainPairViewWithAllowAny.as_view(), name = 'token_obtain_pair'),
    path('api/token/refresh/', api_views.TokenRefreshViewWithAllowAny.as_view(), name = 'token_refresh'),
    # Plaid authentication endpoints
    path("plaid/link-token/", api_views.PlaidAuthLinkTokenView.as_view(), name="plaid_auth_link_token"),
    path("plaid/exchange/", api_views.PlaidAuthExchangeView.as_view(), name="plaid_auth_exchange"),
]