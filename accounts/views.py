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
    
    # Calculate stats
    pending_count = user_applications.filter(status='pending').count()
    accepted_count = user_applications.filter(status='accepted').count()
    rejected_count = user_applications.filter(status='rejected').count()
    
    context = {
        'applications': user_applications,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
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
    from grants.models import Grant
    
    applications = Application.objects.all()
    
    stats = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'accepted': applications.filter(status='accepted').count(),
        'rejected': applications.filter(status='rejected').count(),
        'total_grants': Grant.objects.filter(is_published=True).count(),
        'active_projects': applications.filter(status='accepted').count(),
    }
    
    # Calculate budget used (sum of salaries from grants of accepted applications)
    accepted_apps = applications.filter(status='accepted')
    budget_used = 0
    for app in accepted_apps:
        try:
            grant = Grant.objects.get(id=app.grant_id)
            budget_used += grant.salary
        except Grant.DoesNotExist:
            pass
    
    stats['budget_used'] = budget_used
    
    return render(request, 'accounts/admin_dashboard.html', {'stats': stats})

def is_admin(user):
    return user.is_authenticated and user.role == "ADMIN"

@user_passes_test(is_admin)
def promote_reviewer(request):
    # Get all users and categorize them
    all_users = User.objects.all()
    users_to_promote = all_users.exclude(role="REVIEWER").exclude(role="ADMIN")
    current_reviewers = all_users.filter(role="REVIEWER")
    
    # Separate by current role
    applicants = users_to_promote.filter(role="APPLICANT")
    grant_managers = users_to_promote.filter(role="GRANT_MANAGER")
    
    # Calculate statistics
    total_users = all_users.count()
    total_reviewers = current_reviewers.count()
    total_promotable = users_to_promote.count()
    
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        
        # Store old role for message
        old_role = user.get_role_display()
        
        user.role = "REVIEWER"
        user.save()
        
        messages.success(request, f"{user.get_full_name()} has been promoted from {old_role} to Reviewer.")
        return redirect("promote_reviewer")

    return render(request, "accounts/promote_reviewer.html", {
        "users_to_promote": users_to_promote,
        "current_reviewers": current_reviewers,
        "applicants": applicants,
        "grant_managers": grant_managers,
        "total_users": total_users,
        "total_reviewers": total_reviewers,
        "total_promotable": total_promotable,
    })