from django.shortcuts import render, redirect


def home(request):
    return render(request, "landing.html")

def login_template(request):
    if request.user.is_authenticated:
        return redirect("dashboard:overview")
    return render(request, "accounts/login.html")

def refund_policy(request):
    return render(request, "legal/refunds.html")

def privacy_policy(request):
    return render(request, "legal/privacy.html")

def terms_of_service(request):
    return render(request, "legal/tos.html")