from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from .models import Application, ReviewAuditLog, QuarterlyReport
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from .models import Application

# Restrict to Admins or Grant Managers
def is_admin_or_grant_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'GRANT_MANAGER']

@login_required
def my_grants(request):
    """View for managing accepted grants"""
    # Get only accepted applications (these are now grants)
    user_grants = Application.objects.filter(
        user_id=request.user.id,
        status='accepted'
    ).order_by('-updated_at')
    
    context = {
        'grants': user_grants,
        'total_grants': user_grants.count(),
    }
    return render(request, 'grants/my_grants.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.role == "ADMIN")
def assign_reviewers(request):
    User = get_user_model()

    applications = Application.objects.all().select_related('reviewer')
    reviewers = User.objects.filter(role='REVIEWER')
    
    # Separate assigned and unassigned applications
    assigned_apps = applications.filter(reviewer__isnull=False)
    unassigned_apps = applications.filter(reviewer__isnull=True)
    
    # Calculate statistics
    total_apps = applications.count()
    total_reviewers = reviewers.count()
    assigned_count = assigned_apps.count()
    unassigned_count = unassigned_apps.count()

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        reviewer_id = request.POST.get("reviewer_id")

        application = get_object_or_404(Application, id=app_id)
        reviewer = get_object_or_404(User, id=reviewer_id)

        application.reviewer = reviewer
        application.save()

        messages.success(request, f"Reviewer {reviewer.get_full_name()} assigned successfully to {application.grant}.")
        return redirect("assign_reviewers")

    return render(request, "applications/assign_reviewers.html", {
        "applications": applications,
        "assigned_apps": assigned_apps,
        "unassigned_apps": unassigned_apps,
        "reviewers": reviewers,
        "total_apps": total_apps,
        "total_reviewers": total_reviewers,
        "assigned_count": assigned_count,
        "unassigned_count": unassigned_count,
    })


def application(request):
    if request.method == 'POST':
        grant_id = request.POST['grant_id']
        grant = request.POST['grant']
        creator = request.POST['creator']
        creator_id = request.POST['creator_id']
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        resume = request.FILES['resume']
        user_id = request.POST['user_id']

        #  Check if user has made inquiry already
        if request.user.is_authenticated:
            user_id = request.user.id
            has_contacted = Application.objects.all().filter(grant_id=grant_id, user_id=user_id)
            if has_contacted:
                messages.error(request, 'You have already applied for this grant')
                return redirect('/grants/' + str(grant_id))    

        apply = Application(grant=grant, grant_id=grant_id, creator=creator, creator_id=creator_id, name=name, email=email, phone=phone, resume=resume, user_id=user_id)

        apply.save()


        messages.success(request, 'Your application has been submitted')
        return redirect('/grants/' + str(grant_id))
    
    else:
        messages.error(request, 'There was an error submitting your application')
        return redirect('/grants/')

@login_required
def reviewer_dashboard(request):
    # Optional filtering
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    applications = Application.objects.all()  # Adjust based on how reviewer is assigned

    if query:
        applications = applications.filter(grant=query)
    if status_filter:
        applications = applications.filter(status=status_filter)

    paginator = Paginator(applications.order_by('created_at'), 10)
    page_number = request.GET.get('page')
    review_applications = paginator.get_page(page_number)

    return render(request, 'accounts/reviewer_dashboard.html', {'review_applications': review_applications})


@login_required
def view_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'applications/view_application.html', {'application': application})

@login_required
@login_required
def review_application(request, pk):
    application = get_object_or_404(Application, pk=pk)

    if request.method == "POST":
        comment = request.POST.get("review_comments", "").strip()
        action = request.POST.get("action")
        new_status = 'accepted' if action == 'approve' else 'rejected'

        application.review_comments = comment
        application.status = new_status
        application.save()

        # Save audit log
        ReviewAuditLog.objects.create(
            application=application,
            reviewer=request.user,
            action=new_status,
            comment=comment,
        )

        # # Send email to applicant
        # send_mail(
        #     subject=f"Your Grant Application has been {new_status.title()}",
        #     message=(
        #         f"Hello {application.name()},\n\n"
        #         f"Your application for the grant '{application.grant}' has been {new_status}.\n\n"
        #         f"Reviewer Comment:\n{comment}\n\n"
        #         f"Thank you for using GrantIQ.\n"
        #     ),
        #     from_email=None,
        #     recipient_list=[application.email],
        #     fail_silently=False,
        # )

        messages.success(request, f"Application #{application.id} has been {new_status}.")
        return redirect('reviewer_dashboard')

    return render(request, 'applications/review_application.html', {
        'application': application
    })

@login_required
def approve_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    application.status = 'accepted'
    application.save()
    messages.success(request, f"Application #{application.pk} approved successfully.")
    return redirect('reviewer_dashboard')


@login_required
def reject_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    application.status = 'rejected'
    application.save()
    messages.warning(request, f"Application #{application.pk} rejected.")
    return redirect('reviewer_dashboard')


@login_required
def application_list(request):
    from grants.models import Grant
    from django.db.models import Sum
    
    applications = Application.objects.all()
    
    # Calculate stats
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
    
    return render(request, 'applications/application_list.html', {
        'applications': applications,
        'stats': stats
    })


@login_required
def upload_quarterly_report(request, app_id):
    application = get_object_or_404(Application, id=app_id)

    if application.email != request.user.email:
        print("Logged-in user:", request.user)
        print("Application applicant:", application.email)
        return HttpResponseForbidden("You are not allowed to upload a report for this application.")

    if application.status != 'accepted':
        messages.error(request, "This application has not been approved yet.")
        return redirect("dashboard")

    if request.method == "POST":
        quarter = request.POST.get("quarter")
        file = request.FILES.get("report_file")

        QuarterlyReport.objects.create(
            application=application,
            quarter=quarter,
            report_file=file
        )
        messages.success(request, "Quarterly report uploaded successfully.")
        return redirect('dashboard')
    
    

    return render(request, 'applications/upload_report.html', {'application': application})


@user_passes_test(lambda u: u.is_authenticated and u.role in ['ADMIN', 'GRANT_MANAGER'])
def monitor_reports(request):
    reports = QuarterlyReport.objects.select_related('application').order_by('-submitted_on')
    
    # Prepare quarterly progress data
    accepted_applications = Application.objects.filter(status='accepted')
    quarterly_progress = []
    
    for app in accepted_applications:
        # Get all reports for this application
        app_reports = QuarterlyReport.objects.filter(application=app)
        
        # Create a dictionary to track which quarters have been submitted
        quarters_submitted = {
            'Q1': app_reports.filter(quarter='Q1').exists(),
            'Q2': app_reports.filter(quarter='Q2').exists(),
            'Q3': app_reports.filter(quarter='Q3').exists(),
            'Q4': app_reports.filter(quarter='Q4').exists(),
        }
        
        quarterly_progress.append({
            'grant_title': app.grant,
            'grantee_name': app.name,
            'quarters': quarters_submitted,
            'total_submitted': sum(1 for q in quarters_submitted.values() if q),
        })
    
    # Calculate statistics for the chart
    quarter_stats = {
        'Q1': sum(1 for item in quarterly_progress if item['quarters']['Q1']),
        'Q2': sum(1 for item in quarterly_progress if item['quarters']['Q2']),
        'Q3': sum(1 for item in quarterly_progress if item['quarters']['Q3']),
        'Q4': sum(1 for item in quarterly_progress if item['quarters']['Q4']),
    }
    
    context = {
        'reports': reports,
        'quarterly_progress': quarterly_progress,
        'quarter_stats': quarter_stats,
        'total_grantees': len(quarterly_progress),
    }
    
    return render(request, 'applications/monitor_reports.html', context)


