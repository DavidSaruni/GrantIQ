from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator
from .choices import location_choices, contract_choices
from .models import Grant 
from .forms import GrantForm  # Import GrantForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
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

            grant.save()
            messages.success(request, 'Grant created successfully.')
            return redirect('admin_dashboard')

        except Exception as e:
            messages.error(request, f'Error creating grant: {str(e)}')
            return redirect('create_grant')

    else:
        return render(request, 'grants/create_grant.html')