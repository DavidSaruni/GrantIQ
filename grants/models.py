import os
from datetime import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags

from grants.utils import unique_slug_for_grant

CONTRACT = (
    ("Part Time", "Part Time"),
    ("Full Time", "Full Time"),
    ("Freelance", "Freelancer"),
    ("Organization", "Organization"),
    ("Individual", "Individual"),
)

LOCATION = (
    ("Nairobi", "Nairobi"),
    ("Mombasa", "Mombasa"),
    ("Kisumu", "Kisumu"),
    ("Nakuru", "Nakuru"),
    ("Eldoret", "Eldoret"),
    ("Kakamega", "Kakamega"),
    ("Nyeri", "Nyeri"),
    ("Remote", "Remote"),
    ("Nationwide", "Nationwide"),
    ("Kenya", "Kenya"),
    ("East Africa", "East Africa"),
    ("Africa", "Africa"),
    ("International", "International"),
)


class Grant(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    company = models.CharField(max_length=200, default="National Research Fund")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    role = models.CharField(max_length=200, blank=True, default="")
    location = models.CharField(choices=LOCATION, max_length=50, default="Nationwide")
    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    grant_date = models.DateTimeField(default=datetime.now, blank=True)
    contract = models.CharField(choices=CONTRACT, max_length=150, default="Organization")
    is_published = models.BooleanField(default=True)
    vacancy = models.CharField(max_length=10, null=True, blank=True)
    experience = models.CharField(max_length=100, blank=True, default="")
    salary = models.IntegerField(default=0)
    deadline = models.DateTimeField(null=True, blank=True)
    main_image = models.ImageField(upload_to="photos/%Y/%m/%d/", blank=True, null=True)

    class Meta:
        ordering = ["-grant_date"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_for_grant(self.title, self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("grant", kwargs={"slug": self.slug})

    @property
    def excerpt(self):
        text = " ".join(strip_tags(self.description or "").split())
        if len(text) <= 220:
            return text
        return text[:220].rsplit(" ", 1)[0] + "…"

    def __str__(self):
        return self.title


class GrantDocument(models.Model):
    grant = models.ForeignKey(
        Grant, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(upload_to="grant_docs/%Y/%m/")
    title = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def save(self, *args, **kwargs):
        if not self.title and self.file:
            self.title = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return os.path.splitext(self.filename)[1].lower()

    @property
    def is_pdf(self):
        return self.extension == ".pdf"

    @property
    def is_image(self):
        return self.extension in {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    def __str__(self):
        return self.title or self.filename


class GrantActivity(models.Model):
    grant = models.ForeignKey(
        Grant, on_delete=models.CASCADE, related_name="activities"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    default_due_days = models.PositiveIntegerField(
        default=30,
        help_text="Days after project start when this activity is due.",
    )
    requires_document = models.BooleanField(
        default=False,
        help_text="If enabled, the grantee must upload a document for this activity.",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.grant.title} - {self.name}"
