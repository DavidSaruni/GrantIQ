from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    #Define a model manager for User model with no username field.

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        #Create and save a User with the given email and password.
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        #Create and save a regular User with the given email and password.
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        #Create and save a SuperUser with the given email and password.
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    #User model.

    username = None
    email = models.EmailField(_('email address'), unique=True)

    # Role field
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        GRANT_MANAGER = "GRANT_MANAGER", "Grant Manager"
        REVIEWER = "REVIEWER", "Reviewer"
        APPLICANT = "APPLICANT", "Applicant"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPLICANT)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class ReviewerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    gender = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=80)
    id_number = models.CharField(max_length=80)
    id_document = models.FileField(upload_to="reviewer_apps/ids/%Y/%m/", blank=True)
    is_pwd = models.BooleanField(default=False)
    pwd_number = models.CharField(max_length=80, blank=True)
    home_county = models.CharField(max_length=80, blank=True)
    ethnicity = models.CharField(max_length=80, blank=True)

    institution = models.CharField(max_length=255)
    highest_qualification = models.CharField(max_length=80)
    years_experience = models.PositiveIntegerField(default=0)
    cv = models.FileField(upload_to="reviewer_apps/cvs/%Y/%m/")
    qualification_document = models.FileField(
        upload_to="reviewer_apps/qualifications/%Y/%m/"
    )
    area_of_expertise = models.TextField()
    ford_categories = models.JSONField(default=list, blank=True)

    privacy_consent = models.BooleanField(default=False)
    conduct_consent = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

