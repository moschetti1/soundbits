from django.shortcuts import render

def login_template(request):
    return render(request, "accounts/login.html")