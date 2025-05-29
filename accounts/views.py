from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from accounts.models import User 
from applications.models import Application
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, "You are now logged in!")

            # ✅ Redirect based on role
            if user.is_superuser or user.is_staff or getattr(user, 'role', '').upper() == 'ADMIN':
                return redirect('admin_dashboard')
            elif getattr(user, 'role', '').upper() == 'REVIEWER':
                return redirect('reviewer_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')
    else:
        return render(request, 'accounts/login.html')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email,password=password)

        if user is not None: # Check if the user is found in db
            auth.login(request,user)
            messages.success(request,"You are now logged in!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')
    else:
        return render(request,'accounts/login.html')

def register(request):
    if request.method == 'POST':
       # Get form values
       first_name = request.POST['first_name']
       last_name = request.POST['last_name']
       email = request.POST['email']
       password = request.POST['password']
       confirm_password  = request.POST['confirm_password']

       # Check if passwords match
       if password == confirm_password:
                # Check if the email in db is equal to the input email 
               if User.objects.filter(email=email).exists():
                   messages.error(request, 'That email is already being used!')
                   return redirect('register') 
               else:
                   # Register the user
                   user = User.objects.create_user(password=password, email=email, first_name=first_name, last_name=last_name)
                   user.save()
                   messages.success(request,'You are now registered and can log in')
                   return redirect('login')
                   

       else:
           messages.error(request , 'Passwords do not match!')
           return redirect('register')
    else:
        return render(request,'accounts/register.html')
        
def logout(request):
    if request.method == "POST":
        auth.logout(request)
        messages.success(request,"You are now logged out")
        return redirect('index')

@login_required()
def dashboard(request):
    user_applications = Application.objects.order_by('-contact_date').filter(user_id=request.user.id)
    
    context = {
        'applications': user_applications
    }
    return render(request,'accounts/dashboard.html', context)

@login_required
def login_redirect_view(request):
    user = request.user

    if user.is_authenticated:
        if user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'ADMIN':
            return redirect('admin')  # Your admin dashboard URL name
        else:
            return redirect('dashboard')  # User dashboard

    return redirect('login')
    
def admin_dashboard(request):
    stats = {
        'total': Application.objects.count(),
        'pending': Application.objects.filter(status='pending').count(),
        'accepted': Application.objects.filter(status='accepted').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    return render(request, 'accounts/admin_dashboard.html', {'stats': stats})

def is_admin(user):
    return user.is_authenticated and user.role == "ADMIN"

@user_passes_test(is_admin)
def promote_reviewer(request):
    users_to_promote = User.objects.exclude(role="REVIEWER")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        user.role = "REVIEWER"
        user.save()
        messages.success(request, f"{user.get_full_name()} has been promoted to Reviewer.")
        return redirect("promote_reviewer")

    return render(request, "accounts/promote_reviewer.html", {
        "users_to_promote": users_to_promote
    })