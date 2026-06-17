
from django.shortcuts import render, redirect, get_object_or_404
from .forms import IdeaForm, InvestorProfileForm,LoginForm
from .models import VideoResource,SignupDetail,Message,InvestorProfile,Idea
from .forms import SignupForm, MessageForm
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseNotFound


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                # Fetch the user from SignupDetail
                user = SignupDetail.objects.get(email=email)
                
                # Check if the password is correct
                if check_password(password, user.password):
                    # Log the user in
                    user_data = {
                        'email': email,
                        'name': user.name,
                        'category': user.category
                    }
                    request.session['user_data'] = user_data  # Store user data in session
                    
                    # Redirect based on the category
                    if user.category == 'entrepreneur':
                        request.session['entrepreneur_email'] = email
                        return redirect('home')
                    elif user.category == 'investor':
                        request.session['investor_email'] = email
                        return redirect('investor_dashboard')
                else:
                    messages.error(request, 'Invalid password')
            except SignupDetail.DoesNotExist:
                messages.error(request, 'User with this email does not exist')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the appropriate dashboard based on the category
            category = form.cleaned_data['category']
            if category == 'entrepreneur':
                request.session['entrepreneur_email'] = form.cleaned_data['email']
                return redirect('home')
            elif category == 'investor':
                request.session['investor_email'] = form.cleaned_data['email']
                return redirect('investor_dashboard')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def success(request):
    return render(request, 'success.html') 

def home(request):
    return render(request, 'index.html')

def message(request):
    return render(request,'message.html')

def register_idea(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.entrepreneur_email = request.session.get('user_data', {}).get('email')
            idea.save()
            return redirect('success')
        else:
            print(form.errors)  # Print errors to console for debugging
    else:
        form = IdeaForm()
    return render(request, 'register.html', {'form': form})

def mentors(request):
    return render(request,'mentors.html')

def chatbot(request):
    return render(request, 'chatbot.html')

def investor_chatbot(request):
    return render(request, 'investor_chatbot.html')

def study(request):
    videos = VideoResource.objects.all()
    return render(request, 'study.html', {'videos': videos})


def save_profile(request):
    if request.method == 'POST':
        form = InvestorProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile_success')  # Ensure 'profile_success' is a valid URL name in your urls.py
    else:
        form = InvestorProfileForm()
    return render(request, 'investor_profile.html', {'form': form})


def profile_success(request):
    return render(request, 'profile_success.html')


def investor_dashboard(request):
    return render(request, 'investor_dashboard.html')

def investor_messages(request):
    return render(request, 'investor_messages.html')

def edit_investor_profile(request):
    user_data = request.session.get('user_data')
    
    if not user_data:
        return redirect('login')  # Redirect to login if user data is not found in the session
    
    user_email = user_data.get('email')
    profile, created = InvestorProfile.objects.get_or_create(email=user_email)
    
    if request.method == 'POST':
        form = InvestorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('investor_dashboard')  # Redirect to dashboard after saving
        else:
            print(form.errors)  # Print errors to console for debugging
    else:
        form = InvestorProfileForm(instance=profile)
    
    return render(request, 'investor_profile.html', {'form': form})

def back(request):
    category = request.session.get('user_data',{}).get('category')
    if category == 'investor':
        return render(request,'investor_dashboard.html')
    elif category =='entrepreneur':
        return render(request, 'base.html')
    else:
        return HttpResponseNotFound(request.session.get('user_data',{}).get('category'))
        


def get_signup_detail_for_user(user):
    # Ensure user is an instance of Django's User model
    if not user.is_authenticated:
        return None
    # Fetch SignupDetail related to the authenticated user
    return get_object_or_404(SignupDetail, email=user.email)


def investor(request):
    email = request.session.get('entrepreneur_email')
    if email:
        try:
            idea = get_object_or_404(Idea,email__email=email)
            entrepreneur_tag = idea.tag
            matching_investors = InvestorProfile.objects.filter(tag=entrepreneur_tag)
        except Idea.DoesNotExist:
            matching_investors = []
    else:
        matching_investors = []

    return render(request, 'investor.html', {'investors': matching_investors})

def investor_matches(request):
    email = request.session.get('investor_email')

    if email:
        try:
            investor = get_object_or_404(InvestorProfile, email=email)
            investor_tag = investor.tag
            matching_entrepreneurs = Idea.objects.filter(tag=investor_tag)
        except InvestorProfile.DoesNotExist:
            matching_entrepreneurs = []
        except Idea.DoesNotExist:
            matching_entrepreneurs = []

    return render(request, 'investor_matches.html', {'entrepreneurs': matching_entrepreneurs})


def chat_view(request, email):
    try:
        recipient = SignupDetail.objects.get(email=email)
    except SignupDetail.DoesNotExist:
        return HttpResponseNotFound("User not found")

    # Use the email stored in the session to get the sender's details
    sender_email = request.session.get('user_data', {}).get('email')
    if not sender_email:
        return HttpResponseNotFound("Sender wakkkanot found")

    try:
        sender = SignupDetail.objects.get(email=sender_email)
    except SignupDetail.DoesNotExist:
        return HttpResponseNotFound("Sender not found")

    messages = Message.objects.filter(
        Q(sender=sender, receiver=recipient) |
        Q(sender=recipient, receiver=sender)
    ).order_by('timestamp')

    form = MessageForm()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                sender=sender,
                receiver=recipient,
                content=form.cleaned_data['content']
            )
            return redirect('chat_view', email=email)

    return render(request, 'chat.html', {'messages': messages, 'form': form, 'recipient': recipient})
