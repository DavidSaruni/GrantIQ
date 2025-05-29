from django.urls import path

from .import views

urlpatterns = [
    path('application' ,  views.application , name = 'application') ,
    # for admins and grant managers
    path('assign-reviewers/', views.assign_reviewers, name='assign_reviewers'),
    path('all/', views.application_list, name='application_list'),


    # for reviewers
    path('reviewer-dashboard/', views.reviewer_dashboard, name='reviewer_dashboard'),
    path('application/<int:pk>/view/', views.view_application, name='view_application'),
    path('application/<int:pk>/review/', views.review_application, name='review_application'),


    path('application/<int:pk>/approve/', views.approve_application, name='approve_application'),
    path('application/<int:pk>/reject/', views.reject_application, name='reject_application'),

    # for applicantss
    #path('application/<int:pk>/edit/', views.edit_application, name='edit_application'),

    path('application/<int:app_id>/upload-report/', views.upload_quarterly_report, name='upload_quarterly_report'),
    path('monitor-reports/', views.monitor_reports, name='monitor_reports'),

]