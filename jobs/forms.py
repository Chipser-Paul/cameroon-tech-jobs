from django import forms
from .models import Job, Category, TechStack


class JobForm(forms.ModelForm):
    tech_stacks = forms.ModelMultipleChoiceField(
        queryset=TechStack.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Tech Stack'
    )
    custom_tech = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add custom tech (comma separated): e.g. Odoo, SAP, MATLAB'
        }),
        label='Custom Technologies'
    )

    class Meta:
        model = Job
        fields = [
            'title', 'category', 'job_type', 'location',
            'experience_level', 'salary_range', 'description',
            'requirements', 'apply_email', 'apply_link',
            'plan', 'tech_stacks'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Python Developer'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 150,000 – 300,000 XAF/month'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe the role and responsibilities...'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'List required skills and qualifications...'}),
            'apply_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hr@yourcompany.com'}),
            'apply_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourcompany.com/apply'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].required = False
        self.fields['salary_range'].required = False
        self.fields['apply_email'].required = False
        self.fields['apply_link'].required = False
        self.fields['experience_level'].required = False

    def save(self, commit=True):
        job = super().save(commit=commit)
        # Handle custom tech stacks
        custom = self.cleaned_data.get('custom_tech', '')
        if custom:
            for tech_name in custom.split(','):
                tech_name = tech_name.strip()
                if tech_name:
                    tech, _ = TechStack.objects.get_or_create(name=tech_name)
                    job.tech_stacks.add(tech)
        return job