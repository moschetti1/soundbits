from django.shortcuts import render


def home(request):
    return render(request, "landing.html")

def login_template(request):
    return render(request, "accounts/login.html")