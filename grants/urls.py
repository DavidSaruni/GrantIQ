from django.urls import path

from .import views

urlpatterns = [
    path('' ,  views.index , name='grants'),
    path('<int:grant_id>', views.grant, name='grant'),
    path('search', views.search, name='search'),
    path('applygrant<int:grant_id>', views.applygrant, name='applygrant_with_grant_id'),

    path('create-grant/', views.create_grant, name='create_grant'),
]