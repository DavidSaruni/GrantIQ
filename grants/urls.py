from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='grants'),
    path('<int:grant_id>', views.grant, name='grant'),
    path('search', views.search, name='search'),
    path('applygrant<int:grant_id>', views.applygrant, name='applygrant_with_grant_id'),
    path('create-grant/', views.create_grant, name='create_grant'),
    path('manage/', views.manage_grants, name='manage_grants'),
    path(
        'grant/<int:grant_id>/activities/',
        views.manage_grant_activities,
        name='manage_grant_activities',
    ),
]