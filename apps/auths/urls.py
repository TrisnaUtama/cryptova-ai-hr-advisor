from django.urls import path
from apps.auths.views import SignInView, SignUpView, DashboardView,SignOut

urlpatterns = [
    path("", SignInView.as_view(), name="sign-in"),
    path("sign-up", SignUpView.as_view(), name="sign-up"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path('sign-out', SignOut.as_view(), name='sign-out'),
]