from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST

from .choices import contract_choices, location_choices
from .models import Grant, GrantActivity, GrantDocument
from .utils import (
    MAX_UPLOAD_BYTES,
    inline_file_response,
    is_allowed_attachment,
    is_allowed_image,
)


def index(request):
    grants = Grant.objects.order_by("-grant_date").filter(is_published=True)

    paginator = Paginator(grants, 10)
    page_number = request.GET.get("page")
    paged_grants = paginator.get_page(page_number)

    context = {"grants": paged_grants}
    return render(request, "grants/grants.html", context)


def grant(request, slug):
    grant = get_object_or_404(Grant, slug=slug, is_published=True)
    documents = grant.documents.all()
    context = {
        "grant": grant,
        "documents": documents,
    }
    return render(request, "grants/grant.html", context)


def grant_by_id_redirect(request, grant_id):
    grant_obj = get_object_or_404(Grant, pk=grant_id)
    return redirect(grant_obj.get_absolute_url(), permanent=True)


@xframe_options_exempt
def preview_document(request, doc_id):
    document = get_object_or_404(GrantDocument, pk=doc_id)
    if not document.file:
        raise Http404("Document not found.")
    return inline_file_response(
        document.file,
        document.filename,
        "application/pdf" if document.is_pdf else None,
    )


def search(request):
    grant_list = Grant.objects.order_by("-grant_date").filter(is_published=True)

    if "role" in request.GET:
        role = request.GET["role"]
        if role:
            from django.db.models import Q

            grant_list = grant_list.filter(
                Q(title__icontains=role) | Q(role__icontains=role) | Q(description__icontains=role)
            )

    if "location" in request.GET:
        location = request.GET["location"]
        if location:
            grant_list = grant_list.filter(location__iexact=location)

    if "contract" in request.GET:
        contract = request.GET["contract"]
        if contract:
            grant_list = grant_list.filter(contract__iexact=contract)

    context = {
        "location_choices": location_choices,
        "contract_choices": contract_choices,
        "grants": grant_list,
        "values": request.GET,
    }
    return render(request, "grants/search.html", context)


@login_required()
def applygrant(request, grant_id):
    grant = get_object_or_404(Grant, pk=grant_id)
    context = {"grant": grant}
    return render(request, "grants/applygrant.html", context)


def _save_attachments(grant, files):
    saved = 0
    for uploaded in files:
        if not uploaded:
            continue
        if not is_allowed_attachment(uploaded.name):
            continue
        if uploaded.size and uploaded.size > MAX_UPLOAD_BYTES:
            continue
        GrantDocument.objects.create(
            grant=grant,
            file=uploaded,
            title=uploaded.name,
        )
        saved += 1
    return saved


def is_admin_or_grant_manager(user):
    return user.is_authenticated and getattr(user, "role", "") in [
        "ADMIN",
        "GRANT_MANAGER",
    ]


@login_required
def create_grant(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = request.POST.get("description") or ""
        company = (request.POST.get("company") or "").strip() or "National Research Fund"
        deadline = request.POST.get("deadline") or None
        main_image = request.FILES.get("main_image")

        if not title:
            messages.error(request, "Please enter a grant title.")
            return redirect("create_grant")

        if not description.strip() or description.strip() in {"<p><br></p>", "<p></p>"}:
            messages.error(request, "Please enter the grant detailed information.")
            return redirect("create_grant")

        if main_image and not is_allowed_image(main_image.name):
            messages.error(request, "Grant image must be JPG, PNG, GIF, or WebP.")
            return redirect("create_grant")

        if main_image and main_image.size > MAX_UPLOAD_BYTES:
            messages.error(request, "Grant image must be 10MB or smaller.")
            return redirect("create_grant")

        parsed_deadline = None
        if deadline:
            try:
                parsed_deadline = datetime.fromisoformat(deadline)
            except ValueError:
                messages.error(request, "Invalid application deadline.")
                return redirect("create_grant")

        try:
            grant = Grant.objects.create(
                creator=request.user,
                company=company,
                title=title,
                description=description,
                deadline=parsed_deadline,
                main_image=main_image,
                grant_date=datetime.now(),
                location="Nationwide",
                contract="Organization",
                role="",
                about="",
                vacancy="",
                experience="",
                salary=0,
            )
            attachments = request.FILES.getlist("attachments")
            _save_attachments(grant, attachments)
            messages.success(request, "Grant created successfully.")
            return redirect(grant.get_absolute_url())
        except Exception as exc:
            messages.error(request, f"Error creating grant: {exc}")
            return redirect("create_grant")

    return render(request, "grants/create_grant.html")


@login_required
@user_passes_test(is_admin_or_grant_manager)
def edit_grant(request, grant_id):
    grant = get_object_or_404(Grant.objects.prefetch_related("documents"), pk=grant_id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = request.POST.get("description") or ""
        company = (request.POST.get("company") or "").strip() or grant.company
        deadline = request.POST.get("deadline") or None
        main_image = request.FILES.get("main_image")

        if not title:
            messages.error(request, "Please enter a grant title.")
            return redirect("edit_grant", grant_id=grant.id)

        if not description.strip() or description.strip() in {"<p><br></p>", "<p></p>"}:
            messages.error(request, "Please enter the grant detailed information.")
            return redirect("edit_grant", grant_id=grant.id)

        if main_image and not is_allowed_image(main_image.name):
            messages.error(request, "Grant image must be JPG, PNG, GIF, or WebP.")
            return redirect("edit_grant", grant_id=grant.id)

        if main_image and main_image.size > MAX_UPLOAD_BYTES:
            messages.error(request, "Grant image must be 10MB or smaller.")
            return redirect("edit_grant", grant_id=grant.id)

        parsed_deadline = grant.deadline
        if deadline:
            try:
                parsed_deadline = datetime.fromisoformat(deadline)
            except ValueError:
                messages.error(request, "Invalid application deadline.")
                return redirect("edit_grant", grant_id=grant.id)

        try:
            grant.title = title
            grant.company = company
            grant.description = description
            grant.deadline = parsed_deadline
            if main_image:
                grant.main_image = main_image
            grant.save()
            _save_attachments(grant, request.FILES.getlist("attachments"))
            messages.success(request, "Grant updated successfully.")
            return redirect("manage_grants")
        except Exception as exc:
            messages.error(request, f"Error updating grant: {exc}")
            return redirect("edit_grant", grant_id=grant.id)

    return render(request, "grants/create_grant.html", {"grant": grant})


@login_required
@user_passes_test(is_admin_or_grant_manager)
@require_POST
def toggle_grant_publish(request, grant_id):
    grant = get_object_or_404(Grant, pk=grant_id)
    grant.is_published = not grant.is_published
    grant.save(update_fields=["is_published"])
    if grant.is_published:
        messages.success(request, f'"{grant.title}" is now published.')
    else:
        messages.success(request, f'"{grant.title}" has been unpublished.')
    return redirect("manage_grants")


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
            requires_document = request.POST.get("requires_document") in (
                "on",
                "1",
                "true",
            )

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
                        requires_document=requires_document,
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
                    activity.requires_document = requires_document
                    activity.save()
                    activity.project_activities.update(
                        requires_document=requires_document
                    )
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
