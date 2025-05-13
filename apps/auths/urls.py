from django.urls import path
from apps.auths.views import SignInView, SignUpView, SignOut

urlpatterns = [
    path("", SignInView.as_view(), name="sign-in"),
    path("sign-up", SignUpView.as_view(), name="sign-up"),
    path("sign-out", SignOut.as_view(), name="sign-out"),
]
