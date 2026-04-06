from django import forms
from .models import Company


class CompanyRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Company
        fields = ['company_name', 'email', 'phone', 'website', 'location', 'description', 'logo']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        if p1 and len(p1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return cleaned_data

    def save(self, commit=True):
        company = super().save(commit=False)
        company.set_password(self.cleaned_data['password1'])
        if commit:
            company.save()
        return company