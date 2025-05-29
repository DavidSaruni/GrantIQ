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
@user_passes_test(lambda u: u.is_staff or u.role == "ADMIN")
def assign_reviewers(request):
    User = get_user_model()

    applications = Application.objects.all()
    reviewers = User.objects.filter(role='REVIEWER')  # Make sure 'role' is a field in your custom User model

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        reviewer_id = request.POST.get("reviewer_id")

        application = get_object_or_404(Application, id=app_id)
        reviewer = get_object_or_404(User, id=reviewer_id)

        application.reviewer = reviewer
        application.save()

        messages.success(request, "Reviewer assigned successfully.")
        return redirect("assign_reviewers")

    return render(request, "applications/assign_reviewers.html", {
        "applications": applications,
        "reviewers": reviewers
    })


def application(request):
    if request.method == 'POST':
        job_id = request.POST['job_id']
        job = request.POST['job']
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
            has_contacted = Application.objects.all().filter(job_id=job_id, user_id=user_id)
            if has_contacted:
                messages.error(request, 'You have already applied for this grant')
                return redirect('/jobs/'+job_id)    

        apply = Application(job=job, job_id=job_id,creator=creator,creator_id=creator_id, name=name, email=email, phone=phone,resume=resume, user_id=user_id)

        apply.save()


        messages.success(request, 'Your application has been submitted')
        return redirect('/jobs/'+ job_id)
    
    else:
        messages.error(request, 'There was an error submitting your application')
        return redirect('/jobs/')

@login_required
def reviewer_dashboard(request):
    # Optional filtering
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    applications = Application.objects.all()  # Adjust based on how reviewer is assigned

    if query:
        applications = applications.filter(job=query)
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
        #         f"Your application for the grant '{application.job}' has been {new_status}.\n\n"
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
    applications = Application.objects.all()
    return render(request, 'applications/application_list.html', {
        'applications': applications
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
    return render(request, 'applications/monitor_reports.html', {'reports': reports})


