from django import forms
from grants.models import Grant

class GrantForm(forms.ModelForm):
    class Meta:
        model = Grant
        fields = '__all__'
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'grant_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }