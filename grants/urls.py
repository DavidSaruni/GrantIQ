from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="grants"),
    path("search", views.search, name="search"),
    path("applygrant<int:grant_id>", views.applygrant, name="applygrant_with_grant_id"),
    path("create-grant/", views.create_grant, name="create_grant"),
    path("manage/", views.manage_grants, name="manage_grants"),
    path(
        "grant/<int:grant_id>/activities/",
        views.manage_grant_activities,
        name="manage_grant_activities",
    ),
    path(
        "grant/<int:grant_id>/edit/",
        views.edit_grant,
        name="edit_grant",
    ),
    path(
        "grant/<int:grant_id>/toggle-publish/",
        views.toggle_grant_publish,
        name="toggle_grant_publish",
    ),
    path(
        "documents/<int:doc_id>/",
        views.preview_document,
        name="grant_document_preview",
    ),
    path("<int:grant_id>/", views.grant_by_id_redirect, name="grant_by_id"),
    path("<int:grant_id>", views.grant_by_id_redirect),
    path("<slug:slug>/", views.grant, name="grant"),
    path("<slug:slug>", views.grant),
]
