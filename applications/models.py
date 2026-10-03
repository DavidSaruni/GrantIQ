from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from grants.models import Grant, GrantActivity


class Application(models.Model):
    grant_id = models.IntegerField()
    grant = models.CharField(max_length=100)
    creator = models.CharField(max_length=200)
    creator_id = models.IntegerField()
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    resume = models.FileField(upload_to="doc", blank=True)
    contact_date = models.DateTimeField(default=datetime.now, blank=True)
    user_id = models.IntegerField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default="pending")
    review_comments = models.TextField(blank=True, null=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_applications",
    )

    def __str__(self):
        return self.name

    @property
    def resume_filename(self):
        if not self.resume:
            return ""
        return self.resume.name.rsplit("/", 1)[-1]

    @property
    def resume_is_pdf(self):
        return (self.resume_filename or "").lower().endswith(".pdf")

    @property
    def resume_is_image(self):
        name = (self.resume_filename or "").lower()
        return name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))


class ApplicationComment(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="discussion_comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application_comments",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.application}"


class ReviewAuditLog(models.Model):
    application = models.ForeignKey(
        "Application", on_delete=models.CASCADE, related_name="audit_logs"
    )
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(
        max_length=10, choices=[("approved", "Approved"), ("rejected", "Rejected")]
    )
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.action} by {self.reviewer}"


class QuarterlyReport(models.Model):
    application = models.ForeignKey(
        "Application", on_delete=models.CASCADE, related_name="reports"
    )
    report_file = models.FileField(upload_to="quarterly_reports/")
    quarter = models.CharField(
        max_length=10,
        choices=[("Q1", "Q1"), ("Q2", "Q2"), ("Q3", "Q3"), ("Q4", "Q4")],
    )
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.quarter}"


class ProjectActivity(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="activities"
    )
    grant_activity = models.ForeignKey(
        GrantActivity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_activities",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submission_file = models.FileField(
        upload_to="project_activities/", null=True, blank=True
    )
    requires_document = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "due_date"]

    @property
    def needs_document(self):
        if self.requires_document:
            return True
        if self.grant_activity_id:
            return bool(self.grant_activity.requires_document)
        return False

    def __str__(self):
        return f"{self.application} - {self.name}"


class ActivityComment(models.Model):
    activity = models.ForeignKey(
        ProjectActivity, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.activity}"

