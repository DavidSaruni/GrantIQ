from django.contrib import admin
from .models import Grant, GrantDocument, GrantActivity


class GrantDocumentInline(admin.TabularInline):
    model = GrantDocument
    extra = 1


class GrantAdmin(admin.ModelAdmin):
    exclude = ("creator",)
    list_display = ("title", "slug", "company", "location", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GrantDocumentInline]
    search_fields = ("title", "company", "slug")

    def get_queryset(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return Grant.objects.all()
        return Grant.objects.filter(creator=request.user)

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        obj.save()


admin.site.register(Grant, GrantAdmin)
admin.site.register(GrantActivity)
