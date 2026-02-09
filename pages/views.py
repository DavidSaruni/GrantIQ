from django.shortcuts import render
from django.http import HttpResponse
from grants.choices import contract_choices, location_choices
from grants.models import Grant

def index(request):
    grants = Grant.objects.order_by('-grant_date').filter(is_published=True)[:3]

    context = {
        'grants': grants,
        'location_choices': location_choices,
        'contract_choices':  contract_choices
    }
    return render(request,'pages/index.html',context)

def about(request):
    return render(request,'pages/about.html')