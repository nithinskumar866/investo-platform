from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password 

class SignupDetail(models.Model):
    CATEGORY_CHOICES = [
        ('entrepreneur', 'Entrepreneur'),
        ('investor', 'Investor'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Store hashed passwords
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only hash the password when creating a new object
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class Idea(models.Model):
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

    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField()
    tag = models.CharField(max_length=50, choices=TAG_CHOICES)
    email = models.ForeignKey(SignupDetail, on_delete=models.CASCADE, related_name='ideas',default="")

    def __str__(self):
        return self.title


class VideoResource(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)

    def _str_(self):
        return self.title

    @property
    def video_source(self):
        if self.video_file:
            return self.video_file.url
        return self.video_url
    
class InvestorProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
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
    tag = models.CharField(max_length=50, choices=TAG_CHOICES,default='')
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def _str_(self):
        return self.name

class Message(models.Model):
    sender = models.ForeignKey(SignupDetail, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(SignupDetail, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.name} -> {self.receiver.name}: {self.content[:20]}"

