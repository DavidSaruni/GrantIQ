from django.urls import path
from .import views

urlpatterns=[
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('become-a-reviewer/', views.become_reviewer, name='become_reviewer'),
]