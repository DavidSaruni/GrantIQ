from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.http import Http404, HttpResponseForbidden
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import (
    Application,
    ApplicationComment,
    ReviewAuditLog,
    QuarterlyReport,
    ProjectActivity,
    ActivityComment,
)

# Restrict to Admins or Grant Managers
def is_admin_or_grant_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'GRANT_MANAGER']


def is_reviewer(user):
    return user.is_authenticated and getattr(user, "role", "") == "REVIEWER"


def _is_application_owner(user, application):
    if not user.is_authenticated:
        return False
    if application.user_id and str(application.user_id) == str(user.id):
        return True
    return bool(
        application.email
        and user.email
        and application.email.lower() == user.email.lower()
    )


def _can_access_application(user, application):
    if not user.is_authenticated:
        return False
    role = getattr(user, "role", "")
    if role in ("ADMIN", "GRANT_MANAGER", "REVIEWER"):
        return True
    return _is_application_owner(user, application)


def _send_application_email(subject, body, recipients):
    recipients = [email for email in recipients if email]
    if not recipients:
        return
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        pass


def _notify_application_comment(request, application, comment):
    author_name = comment.author.get_full_name() or comment.author.email
    is_owner = _is_application_owner(comment.author, application)
    if is_owner:
        if not application.reviewer or not application.reviewer.email:
            return
        link = request.build_absolute_uri(
            reverse("review_application", args=[application.pk])
        )
        _send_application_email(
            f"Applicant reply on {application.grant}",
            (
                f"Hello {application.reviewer.get_full_name() or 'Reviewer'},\n\n"
                f"{author_name} replied on the proposal for '{application.grant}'.\n\n"
                f"Comment:\n{comment.message}\n\n"
                f"Open the review page:\n{link}\n\n"
                f"GrantIQ"
            ),
            [application.reviewer.email],
        )
        return

    link = request.build_absolute_uri(
        reverse("application_discussion", args=[application.pk])
    )
    _send_application_email(
        f"Reviewer comment on your {application.grant} application",
        (
            f"Hello {application.name},\n\n"
            f"{author_name} commented on your proposal for '{application.grant}'.\n\n"
            f"Comment:\n{comment.message}\n\n"
            f"Read and reply in your GrantIQ dashboard:\n{link}\n\n"
            f"GrantIQ"
        ),
        [application.email],
    )


def _notify_application_decision(request, application, new_status, remarks):
    link = request.build_absolute_uri(
        reverse("application_discussion", args=[application.pk])
    )
    _send_application_email(
        f"Your GrantIQ application has been {new_status}",
        (
            f"Hello {application.name},\n\n"
            f"Your application for '{application.grant}' has been {new_status}.\n\n"
            f"Reviewer remarks:\n{remarks}\n\n"
            f"View the discussion and decision in your dashboard:\n{link}\n\n"
            f"GrantIQ"
        ),
        [application.email],
    )


def _add_application_comment(request, application):
    message = (request.POST.get("message") or "").strip()
    if not message:
        messages.error(request, "Please enter a comment.")
        return False
    comment = ApplicationComment.objects.create(
        application=application,
        author=request.user,
        message=message,
    )
    _notify_application_comment(request, application, comment)
    messages.success(request, "Comment sent. The other party has been notified by email.")
    return True

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
        action = request.POST.get("action")

        if action == "add_reviewer":
            full_name = request.POST.get("name", "").strip()
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not full_name or not email or not password or not confirm_password:
                messages.error(request, "All fields are required to add a reviewer.")
                return redirect("assign_reviewers")

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("assign_reviewers")

            if User.objects.filter(email=email).exists():
                messages.error(request, "A user with this email already exists.")
                return redirect("assign_reviewers")

            # Split full name into first and last name
            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            reviewer = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=User.Role.REVIEWER,
            )

            # Send credentials email
            try:
                login_url = request.build_absolute_uri(reverse("login"))
            except Exception:
                login_url = ""

            message = (
                f"Hello {full_name},\n\n"
                f"You have been added as a reviewer on GrantIQ.\n\n"
                f"Login URL: {login_url}\n"
                f"Email: {email}\n"
                f"Password: {password}\n\n"
                f"For security, please log in and change your password after your first login."
            )

            send_mail(
                subject="Your GrantIQ Reviewer Account",
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=True,
            )

            messages.success(
                request,
                f"Reviewer {reviewer.get_full_name()} created successfully and login credentials emailed.",
            )
            return redirect("assign_reviewers")

        # Default: assign existing reviewer to application
        app_id = request.POST.get("application_id")
        reviewer_id = request.POST.get("reviewer_id")

        application = get_object_or_404(Application, id=app_id)
        reviewer = get_object_or_404(User, id=reviewer_id)

        application.reviewer = reviewer
        application.save()

        messages.success(
            request,
            f"Reviewer {reviewer.get_full_name()} assigned successfully to {application.grant}.",
        )
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

        from grants.models import Grant as GrantModel

        def grant_redirect(gid):
            try:
                return GrantModel.objects.get(pk=gid).get_absolute_url()
            except GrantModel.DoesNotExist:
                return "/grants/"

        #  Check if user has made inquiry already
        if request.user.is_authenticated:
            user_id = request.user.id
            has_contacted = Application.objects.all().filter(grant_id=grant_id, user_id=user_id)
            if has_contacted:
                messages.error(request, 'You have already applied for this grant')
                return redirect(grant_redirect(grant_id))

        apply = Application(grant=grant, grant_id=grant_id, creator=creator, creator_id=creator_id, name=name, email=email, phone=phone, resume=resume, user_id=user_id)

        apply.save()


        messages.success(request, 'Your application has been submitted')
        return redirect(grant_redirect(grant_id))
    
    else:
        messages.error(request, 'There was an error submitting your application')
        return redirect('/grants/')

@login_required
@user_passes_test(is_reviewer)
def reviewer_dashboard(request):
    # Optional filtering
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    applications = Application.objects.filter(reviewer=request.user)

    total_assigned = applications.count()
    pending_count = applications.filter(status="pending").count()
    reviewed_count = applications.exclude(status="pending").count()

    if query:
        applications = applications.filter(grant__icontains=query)
    if status_filter:
        applications = applications.filter(status=status_filter)

    paginator = Paginator(applications.order_by('created_at'), 10)
    page_number = request.GET.get('page')
    review_applications = paginator.get_page(page_number)

    context = {
        "review_applications": review_applications,
        "total_assigned": total_assigned,
        "pending_count": pending_count,
        "reviewed_count": reviewed_count,
    }

    return render(request, 'accounts/reviewer_dashboard.html', context)


@login_required
def view_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'applications/view_application.html', {'application': application})

@login_required
@user_passes_test(is_reviewer)
def review_application(request, pk):
    application = get_object_or_404(Application, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "comment":
            _add_application_comment(request, application)
            return redirect("review_application", pk=application.pk)

        if action not in ("approve", "reject"):
            messages.error(request, "Choose a valid review action.")
            return redirect("review_application", pk=application.pk)

        remarks = (request.POST.get("review_comments") or "").strip()
        if not remarks:
            messages.error(request, "Please add final remarks before approving or rejecting.")
            return redirect("review_application", pk=application.pk)

        new_status = "accepted" if action == "approve" else "rejected"
        application.review_comments = remarks
        application.status = new_status
        application.save()

        ReviewAuditLog.objects.create(
            application=application,
            reviewer=request.user,
            action=new_status,
            comment=remarks,
        )
        _notify_application_decision(request, application, new_status, remarks)
        messages.success(request, f"Application #{application.id} has been {new_status}.")

        if new_status == "accepted":
            from grants.models import GrantActivity, Grant

            try:
                grant = Grant.objects.get(id=application.grant_id)
                templates = GrantActivity.objects.filter(grant=grant).order_by("order")
                for template in templates:
                    due_date = None
                    if template.default_due_days:
                        due_date = (
                            timezone.now()
                            + timezone.timedelta(days=template.default_due_days)
                        ).date()
                    ProjectActivity.objects.get_or_create(
                        application=application,
                        grant_activity=template,
                        defaults={
                            "name": template.name,
                            "description": template.description,
                            "order": template.order,
                            "due_date": due_date,
                            "requires_document": template.requires_document,
                        },
                    )
            except Grant.DoesNotExist:
                pass

        return redirect("reviewer_dashboard")

    comments = application.discussion_comments.select_related("author")
    return render(
        request,
        "applications/review_application.html",
        {
            "application": application,
            "comments": comments,
            "can_reply": application.status == "pending",
        },
    )


@login_required
def application_discussion(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if not _can_access_application(request.user, application):
        return HttpResponseForbidden("You cannot access this application.")

    if request.method == "POST":
        if application.status != "pending" and not is_admin_or_grant_manager(request.user):
            messages.error(request, "This application is no longer open for discussion.")
            return redirect("application_discussion", pk=application.pk)
        _add_application_comment(request, application)
        return redirect("application_discussion", pk=application.pk)

    comments = application.discussion_comments.select_related("author")
    template = (
        "applications/review_application.html"
        if getattr(request.user, "role", "") in ("REVIEWER", "ADMIN", "GRANT_MANAGER")
        and not _is_application_owner(request.user, application)
        else "applications/application_discussion.html"
    )
    if template == "applications/review_application.html":
        return redirect("review_application", pk=application.pk)

    return render(
        request,
        "applications/application_discussion.html",
        {
            "application": application,
            "comments": comments,
            "can_reply": application.status == "pending",
        },
    )


@login_required
@xframe_options_exempt
def preview_application_proposal(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if not _can_access_application(request.user, application):
        return HttpResponseForbidden("You cannot view this proposal.")
    if not application.resume:
        raise Http404("Proposal not found.")
    from grants.utils import inline_file_response

    return inline_file_response(
        application.resume,
        application.resume_filename,
        "application/pdf" if application.resume_is_pdf else None,
    )

@login_required
@user_passes_test(is_reviewer)
def approve_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    application.status = 'accepted'
    application.save()
    messages.success(request, f"Application #{application.pk} approved successfully.")

    # Initialize project activities when approved directly
    from grants.models import GrantActivity, Grant

    try:
        grant = Grant.objects.get(id=application.grant_id)
        templates = GrantActivity.objects.filter(grant=grant).order_by("order")
        for template in templates:
            due_date = None
            if template.default_due_days:
                due_date = (timezone.now() + timezone.timedelta(days=template.default_due_days)).date()
            ProjectActivity.objects.get_or_create(
                application=application,
                grant_activity=template,
                defaults={
                    "name": template.name,
                    "description": template.description,
                    "order": template.order,
                    "due_date": due_date,
                    "requires_document": template.requires_document,
                },
            )
    except Grant.DoesNotExist:
        pass

    return redirect('reviewer_dashboard')


@login_required
@user_passes_test(is_reviewer)
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
    # Monitoring & evaluation based on project activities
    accepted_applications = Application.objects.filter(status="accepted")

    projects = []
    for app in accepted_applications:
        activities = ProjectActivity.objects.filter(application=app)
        total_activities = activities.count()
        completed_activities = activities.filter(status="approved").count()
        submitted_activities = activities.filter(status="submitted").count()

        projects.append(
            {
                "application": app,
                "total_activities": total_activities,
                "completed_activities": completed_activities,
                "submitted_activities": submitted_activities,
            }
        )

    context = {
        "projects": projects,
    }

    return render(request, "applications/monitor_reports.html", context)


def _can_access_project(user, application):
    if getattr(user, "role", "") in ["ADMIN", "GRANT_MANAGER"]:
        return True
    return application.user_id == user.id or application.email == user.email


@login_required
def project_activities(request, app_id):
    application = get_object_or_404(Application, pk=app_id)
    if not _can_access_project(request.user, application):
        return HttpResponseForbidden("You cannot view these project activities.")

    activities = ProjectActivity.objects.filter(application=application).select_related(
        "grant_activity"
    )
    completed_count = activities.filter(status="approved").count()
    pending_count = activities.exclude(status="approved").count()
    return render(
        request,
        "applications/project_activities.html",
        {
            "application": application,
            "activities": activities,
            "completed_count": completed_count,
            "pending_count": pending_count,
        },
    )


@login_required
def project_activity_detail(request, activity_id):
    activity = get_object_or_404(
        ProjectActivity.objects.select_related("application", "grant_activity"),
        pk=activity_id,
    )
    if not _can_access_project(request.user, activity.application):
        return HttpResponseForbidden("You cannot view this activity.")

    is_grantee = (
        activity.application.user_id == request.user.id
        or activity.application.email == request.user.email
    )
    is_manager = getattr(request.user, "role", "") in ["ADMIN", "GRANT_MANAGER"]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "submit" and is_grantee:
            uploaded = request.FILES.get("submission_file")
            if activity.needs_document and not uploaded and not activity.submission_file:
                messages.error(request, "Please upload a document for this activity.")
            else:
                if uploaded:
                    activity.submission_file = uploaded
                activity.status = "submitted"
                activity.submitted_at = timezone.now()
                activity.save()
                messages.success(request, "Activity submitted successfully.")
            return redirect("project_activity_detail", activity_id=activity.id)

        if action == "review" and is_manager:
            decision = request.POST.get("decision")
            comment = (request.POST.get("review_comment") or "").strip()
            if decision == "approve":
                activity.status = "approved"
                activity.reviewed_at = timezone.now()
                activity.save()
                messages.success(request, "Activity approved.")
            elif decision == "reject":
                activity.status = "rejected"
                activity.reviewed_at = timezone.now()
                activity.save()
                messages.warning(request, "Activity rejected.")
            else:
                messages.error(request, "Select a review decision.")
            if comment:
                ActivityComment.objects.create(
                    activity=activity, author=request.user, message=comment
                )
            return redirect("project_activity_detail", activity_id=activity.id)

        if action == "comment":
            message = (request.POST.get("message") or "").strip()
            if message:
                ActivityComment.objects.create(
                    activity=activity, author=request.user, message=message
                )
                messages.success(request, "Comment posted.")
            return redirect("project_activity_detail", activity_id=activity.id)

    comments = activity.comments.select_related("author").all()
    base_template = (
        "admin_base.html" if is_manager else "user_base.html"
    )
    return render(
        request,
        "applications/project_activity_detail.html",
        {
            "activity": activity,
            "comments": comments,
            "base_template": base_template,
            "is_grantee": is_grantee,
            "is_manager": is_manager,
        },
    )



