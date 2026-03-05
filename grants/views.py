from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .choices import location_choices, contract_choices
from .models import Grant, GrantActivity
from .forms import GrantForm  # Import GrantForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import datetime

def index(request):
    grants = Grant.objects.order_by('-grant_date').filter(is_published = True) # Fetching data from db

    paginator = Paginator(grants,3) 
    page_number = request.GET.get('page')
    paged_grants = paginator.get_page(page_number)

    context = {
        'grants': paged_grants
    }
    return render (request , 'grants/grants.html', context)


def grant(request,grant_id):
     #If user searches for an invalid grant , display a 404 error page

    grant = get_object_or_404(Grant , pk=grant_id)

    context = {
        'grant': grant
    }

    return render (request , 'grants/grant.html',context)

def search(request):
    grant_list = Grant.objects.order_by('-grant_date')


    if 'role' in request.GET:
        role = request.GET['role']
        if role:
            grant_list = grant_list.filter(role__icontains = role)


    if 'location' in request.GET:
        location = request.GET['location']
        if location:
           grant_list = grant_list.filter(location__iexact = location)
     

    if 'contract' in request.GET:
        contract = request.GET['contract']
        if contract:
            grant_list = grant_list.filter(contract__iexact = contract)


    context = {
        'location_choices': location_choices,
        'contract_choices': contract_choices,
        'grants': grant_list,
        'values': request.GET # preserving form inputs 

    }
    return render (request , 'grants/search.html',context)

@login_required()
def applygrant(request,grant_id):
    grant = get_object_or_404(Grant , pk=grant_id)
    # if deadline >= datetime.now():
    #     messages.error(request, 'Deadline is done')
    #     return redirect('/grants/'+grant_id)    

    context = {
        'grant': grant
    }
    return render(request,'grants/applygrant.html',context)

@login_required
def create_grant(request):
    if request.method == 'POST':
        try:
            company = request.POST['company']
            title = request.POST['title']
            role = request.POST['role']
            location = request.POST['location']
            description = request.POST['description']
            about = request.POST['about']
            contract = request.POST['contract']
            vacancy = request.POST['vacancy']
            experience = request.POST['experience']
            salary = request.POST['salary']
            deadline = request.POST['deadline']
            main_image = request.FILES.get('main_image')

            # Validation (basic)
            if not company or not title or not role or not location or not contract:
                messages.error(request, 'Please fill all required fields.')
                return redirect('create_grant')

            grant = Grant.objects.create(
                creator=request.user,
                company=company,
                title=title,
                role=role,
                location=location,
                description=description,
                about=about,
                contract=contract,
                vacancy=vacancy,
                experience=experience,
                salary=salary,
                deadline=deadline,
                main_image=main_image,
                grant_date=datetime.now()
            )

            messages.success(request, 'Grant created successfully.')
            return redirect('admin_dashboard')

        except Exception as e:
            messages.error(request, f'Error creating grant: {str(e)}')
            return redirect('create_grant')

    else:
        return render(request, 'grants/create_grant.html')


def is_admin_or_grant_manager(user):
    return user.is_authenticated and getattr(user, "role", "") in ["ADMIN", "GRANT_MANAGER"]


@login_required
@user_passes_test(is_admin_or_grant_manager)
def manage_grants(request):
    from applications.models import Application

    grants = Grant.objects.all().order_by("-grant_date")

    grant_rows = []
    for grant in grants:
        accepted_projects = Application.objects.filter(
            status="accepted", grant_id=grant.id
        )
        grant_rows.append(
            {
                "grant": grant,
                "accepted_count": accepted_projects.count(),
                "accepted_projects": accepted_projects,
            }
        )

    context = {
        "grant_rows": grant_rows,
        "total_grants": len(grant_rows),
        "total_accepted_projects": sum(r["accepted_count"] for r in grant_rows),
    }

    return render(request, "grants/manage_grants.html", context)


@login_required
@user_passes_test(is_admin_or_grant_manager)
def manage_grant_activities(request, grant_id):
    grant = get_object_or_404(Grant, pk=grant_id)

    activity_to_edit = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action in ["add", "update"]:
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            order = request.POST.get("order") or 1
            default_due_days = request.POST.get("default_due_days") or 30

            if not name:
                messages.error(request, "Activity name is required.")
            else:
                if action == "add":
                    GrantActivity.objects.create(
                        grant=grant,
                        name=name,
                        description=description,
                        order=int(order),
                        default_due_days=int(default_due_days),
                    )
                    messages.success(request, "Activity added successfully.")
                else:
                    activity_id = request.POST.get("activity_id")
                    activity = get_object_or_404(
                        GrantActivity, pk=activity_id, grant=grant
                    )
                    activity.name = name
                    activity.description = description
                    activity.order = int(order)
                    activity.default_due_days = int(default_due_days)
                    activity.save()
                    messages.success(request, "Activity updated successfully.")
            return redirect("manage_grant_activities", grant_id=grant.id)

        elif action == "delete":
            activity_id = request.POST.get("activity_id")
            activity = get_object_or_404(GrantActivity, pk=activity_id, grant=grant)
            activity.delete()
            messages.success(request, "Activity deleted successfully.")
            return redirect("manage_grant_activities", grant_id=grant.id)

        elif action == "edit":
            activity_id = request.POST.get("activity_id")
            activity_to_edit = get_object_or_404(
                GrantActivity, pk=activity_id, grant=grant
            )

    activities = GrantActivity.objects.filter(grant=grant).order_by("order")

    return render(
        request,
        "grants/manage_grant_activities.html",
        {"grant": grant, "activities": activities, "activity_to_edit": activity_to_edit},
    )