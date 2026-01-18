from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.role == "ADMIN":
                return redirect("admin_dashboard")
            elif user.role == "TEACHER":
                return redirect("teacher_dashboard")
            elif user.role == "STUDENT":
                return redirect("student_dashboard")

        return render(request, "login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "login.html")



def logout_view(request):
    logout(request)
    return redirect("login")



def home_view(request):
    return render(request, "base.html")