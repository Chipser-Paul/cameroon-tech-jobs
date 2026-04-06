from django import forms
from .models import Seeker
from jobs.models import TechStack, Category


class SeekerRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Min. 8 characters'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat password'}))

    class Meta:
        model = Seeker
        fields = ['full_name', 'email', 'phone', 'location']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 6XX XXX XXX'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Douala'}),
        }

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
        seeker = super().save(commit=False)
        seeker.set_password(self.cleaned_data['password1'])
        if commit:
            seeker.save()
        return seeker


class SeekerProfileForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=TechStack.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    preferred_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Seeker
        fields = [
            'full_name', 'phone', 'location', 'bio',
            'profile_photo', 'experience_level', 'availability',
            'github', 'portfolio', 'linkedin',
            'skills', 'preferred_categories', 'preferred_locations',
            'job_alerts_enabled'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell companies about yourself...'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'github': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username'}),
            'portfolio': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourportfolio.com'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'preferred_locations': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Douala, Remote'}),
            'job_alerts_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }