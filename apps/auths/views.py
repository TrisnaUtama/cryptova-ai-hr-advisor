from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from core.utils import LoginCheckMixin


# Login Views
class SignInView(View):
    def get(self, request):
        return render(request, "auth/sign-in.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "All fields are required")
            return render(request, "auth/sign-in.html")

        authenticate_user = authenticate(request, username=username, password=password)

        if authenticate_user is None:
            messages.error(request, "Invalid Credentials")
            return render(request, "auth/sign-in.html")

        login(request, authenticate_user)
        return redirect("dashboard")


# End of Login View


# Register Views
class SignUpView(View):
    def get(self, request):
        return render(request, "auth/sign-up.html")

    def post(self, request):
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required")
            return render(request, "auth/sign-up.html")

        if password != confirm_password:
            messages.error(request, "Password doesn't match")
            return render(request, "auth/sign-up.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return render(request, "auth/sign-up.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already sign-uped")
            return render(request, "auth/sign-up.html")

        User.objects.create_user(username=username, email=email, password=password)

        messages.success(request, "Successfuly Sign Up continue to Sign In.")
        return redirect("sign-in")


# End of Register View


# Sign Out View
class SignOut(LoginCheckMixin, View):
    def post(self, request):
        logout(request)
        return redirect("sign-in")
