from django.db import models
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from jobs.models import Job

class Application(models.Model):
  
  job = models.CharField(max_length=100)
  job_id = models.IntegerField()
  creator = models.CharField(max_length=200)
  creator_id = models.IntegerField()
  name = models.CharField(max_length=100)
  email = models.CharField(max_length=100)
  phone = models.CharField(max_length=100)
  resume = models.FileField(upload_to='doc', blank=True)
  contact_date = models.DateTimeField(default=datetime.now, blank=True)
  user_id = models.IntegerField(blank=True)
  created_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  status = models.CharField(max_length=20, default='pending')
  review_comments = models.TextField(blank=True, null=True)
  reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_applications'
    )

  # Main field to be displayed 
  def __str__(self):
    return self.name
  

class ReviewAuditLog(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='audit_logs')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=[('approved', 'Approved'), ('rejected', 'Rejected')])
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.action} by {self.reviewer}"
    

class QuarterlyReport(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='reports')
    report_file = models.FileField(upload_to='quarterly_reports/')
    quarter = models.CharField(max_length=10, choices=[
        ('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')
    ])
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.quarter}"

