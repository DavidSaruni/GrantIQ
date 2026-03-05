from django.db import models
from datetime import datetime, timedelta
from django.conf import settings

CONTRACT = (
    ("Part Time", "Part Time"),
    ("Full Time", "Full Time"),
    ("Freelance", "Freelancer"),
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
)


class Grant(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    company = models.CharField(max_length=200, default=None)
    title = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    location = models.CharField(choices=LOCATION, max_length=50)
    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    grant_date = models.DateTimeField(default=datetime.now, blank=True)
    contract = models.CharField(choices=CONTRACT, max_length=150)
    is_published = models.BooleanField(default=True)
    vacancy = models.CharField(max_length=10, null=True)
    experience = models.CharField(max_length=100)
    salary = models.IntegerField()
    deadline = models.DateTimeField()
    main_image = models.ImageField(upload_to="photos/%Y/%m%d/")

    def __str__(self):
        return self.title


class GrantActivity(models.Model):
    grant = models.ForeignKey(
        Grant, on_delete=models.CASCADE, related_name="activities"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    # Optional relative deadline: days after grant acceptance / project start
    default_due_days = models.PositiveIntegerField(
        default=30,
        help_text="Days after project start when this activity is due.",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.grant.title} - {self.name}"