from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.ford import (
    ETHNICITIES,
    FORD_CATEGORIES,
    KENYA_COUNTIES,
    NATIONALITIES,
    QUALIFICATIONS,
)
from accounts.models import ReviewerApplication
from grants.choices import contract_choices, location_choices
from grants.models import Grant


def index(request):
    grants = Grant.objects.order_by("-grant_date").filter(is_published=True)[:3]

    context = {
        "grants": grants,
        "location_choices": location_choices,
        "contract_choices": contract_choices,
    }
    return render(request, "pages/index.html", context)


def about(request):
    return render(request, "pages/about.html")


def _is_pdf(uploaded):
    if not uploaded:
        return False
    name = (uploaded.name or "").lower()
    return name.endswith(".pdf")


def become_reviewer(request):
    form_context = {
        "ford_categories": FORD_CATEGORIES,
        "counties": KENYA_COUNTIES,
        "ethnicities": ETHNICITIES,
        "nationalities": NATIONALITIES,
        "qualifications": QUALIFICATIONS,
    }

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        privacy = request.POST.get("privacy_consent") == "on"
        conduct = request.POST.get("conduct_consent") == "on"
        ford = request.POST.getlist("ford_categories")
        cv = request.FILES.get("cv")
        qualification_document = request.FILES.get("qualification_document")
        id_document = request.FILES.get("id_document")

        errors = []
        if not privacy:
            errors.append("Please accept the Data Protection & Privacy Notice.")
        if not conduct:
            errors.append("Please confirm the reviewer code of conduct.")
        if not first_name or not last_name or not email:
            errors.append("First name, last name, and email are required.")
        if not ford:
            errors.append("Select at least one FORD research category.")
        if not cv or not _is_pdf(cv):
            errors.append("Please upload your CV as a PDF.")
        if not qualification_document or not _is_pdf(qualification_document):
            errors.append("Please upload your highest qualification document as a PDF.")
        if id_document and not _is_pdf(id_document):
            errors.append("Identification document must be a PDF.")

        if ReviewerApplication.objects.filter(
            email=email, status=ReviewerApplication.Status.PENDING
        ).exists():
            errors.append("A pending reviewer application already exists for this email.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "pages/become_reviewer.html", form_context)

        ReviewerApplication.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=(request.POST.get("phone") or "").strip(),
            gender=(request.POST.get("gender") or "").strip(),
            nationality=(request.POST.get("nationality") or "").strip(),
            id_number=(request.POST.get("id_number") or "").strip(),
            id_document=id_document,
            is_pwd=request.POST.get("is_pwd") == "Yes",
            pwd_number=(request.POST.get("pwd_number") or "").strip(),
            home_county=(request.POST.get("home_county") or "").strip(),
            ethnicity=(request.POST.get("ethnicity") or "").strip(),
            institution=(request.POST.get("institution") or "").strip(),
            highest_qualification=(request.POST.get("highest_qualification") or "").strip(),
            years_experience=int(request.POST.get("years_experience") or 0),
            cv=cv,
            qualification_document=qualification_document,
            area_of_expertise=(request.POST.get("area_of_expertise") or "").strip(),
            ford_categories=ford,
            privacy_consent=True,
            conduct_consent=True,
        )
        messages.success(
            request,
            "Your reviewer application has been submitted. GrantIQ will contact you after review.",
        )
        return redirect("become_reviewer")

    return render(request, "pages/become_reviewer.html", form_context)
