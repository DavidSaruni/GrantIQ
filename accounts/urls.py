from django.urls import path
from .import views
from .views import login_redirect_view

urlpatterns=[
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('register', views.register, name='register'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('route/', login_redirect_view, name='login_redirect'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('promote-reviewer/', views.promote_reviewer, name='promote_reviewer'),
    path('reviewer-applications/', views.reviewer_applications, name='reviewer_applications'),


]