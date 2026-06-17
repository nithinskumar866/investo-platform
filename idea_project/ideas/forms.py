from django import forms
from .models import Idea, InvestorProfile, SignupDetail, Message

TAG_CHOICES = [
    ('Technology', 'Technology'),
    ('Health', 'Health'),
    ('Finance', 'Finance'),
    ('Education', 'Education'),
    ('Environment', 'Environment'),
    ('Marketing', 'Marketing'),
    ('Startups', 'Startups'),
    ('Sustainability', 'Sustainability'),
    ('AI', 'AI'),
    ('Blockchain', 'Blockchain'),
    ('E-commerce', 'E-commerce'),
    ('Social Media', 'Social Media'),
    ('Cybersecurity', 'Cybersecurity'),
    ('Robotics', 'Robotics'),
    ('Fintech', 'Fintech'),
    ('Legal Tech', 'Legal Tech'),
    ('Gaming', 'Gaming'),
    ('Augmented Reality', 'Augmented Reality'),
    ('Virtual Reality', 'Virtual Reality'),
    ('Travel', 'Travel'),
    ('Real Estate', 'Real Estate'),
    ('Food & Beverage', 'Food & Beverage'),
    ('Telecommunications', 'Telecommunications'),
]


class IdeaForm(forms.ModelForm):
    email = forms.ModelChoiceField(
        queryset=SignupDetail.objects.all(),
        to_field_name='email',  # Use 'email' to filter
        empty_label="Email"
    )

    class Meta:
        model = Idea
        fields = ['name', 'title', 'description', 'tag', 'email']


class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ['name', 'email', 'tag']
    
    tag = forms.ChoiceField(
        choices=InvestorProfile.TAG_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
    )

class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class SignupForm(forms.ModelForm):
    class Meta:
        model = SignupDetail
        fields = ['name', 'email', 'password', 'category']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }