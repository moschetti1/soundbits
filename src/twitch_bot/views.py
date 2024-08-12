from django.shortcuts import render, redirect


def home(request):
    return render(request, "landing.html")

def login_template(request):
    if request.user.is_authenticated:
        return redirect("dashboard:overview")
    return render(request, "accounts/login.html")