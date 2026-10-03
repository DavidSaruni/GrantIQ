from django.urls import path

from . import views

urlpatterns = [
    path('application', views.application, name='application'),

    # for admins and grant managers
    path('assign-reviewers/', views.assign_reviewers, name='assign_reviewers'),
    path('all/', views.application_list, name='application_list'),

    # for reviewers
    path('reviewer-dashboard/', views.reviewer_dashboard, name='reviewer_dashboard'),
    path('application/<int:pk>/view/', views.view_application, name='view_application'),
    path('application/<int:pk>/review/', views.review_application, name='review_application'),
    path('application/<int:pk>/discussion/', views.application_discussion, name='application_discussion'),
    path('application/<int:pk>/proposal/', views.preview_application_proposal, name='application_proposal_preview'),
    path('application/<int:pk>/approve/', views.approve_application, name='approve_application'),
    path('application/<int:pk>/reject/', views.reject_application, name='reject_application'),

    # for applicants
    path('my-grants/', views.my_grants, name='my_grants'),
    path('application/<int:app_id>/upload-report/', views.upload_quarterly_report, name='upload_quarterly_report'),
    path('application/<int:app_id>/activities/', views.project_activities, name='project_activities'),
    path('activities/<int:activity_id>/', views.project_activity_detail, name='project_activity_detail'),
    path('monitor-reports/', views.monitor_reports, name='monitor_reports'),
]

