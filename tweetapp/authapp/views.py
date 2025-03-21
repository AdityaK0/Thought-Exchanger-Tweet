from django.shortcuts import render,redirect
from django.contrib.auth import logout,authenticate,login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import re
from allauth.socialaccount.models import SocialAccount

def home(request):
    if request.user.is_authenticated:
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            google_data = social_account.extra_data  
            print(google_data)
            name = google_data.get('name', 'No name found')
            email = google_data.get('email', 'No email found')
            gender = google_data.get('gender','Gender Not Provided')

            context = {
                'google_account_data': {
                    'name': name,
                    'email': email,
                    'gender':gender
                }
            }
        except SocialAccount.DoesNotExist:
            context = {
                'google_account_data': None
            }
    else:
        context = {}

    return render(request, 'index.html', context)


def register(request):
    if request.method == "POST":
        email_id = request.POST.get('email')
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = email_id
            form.save()
            return redirect("login_user")
    else:
        form = UserCreationForm()

    return render(request,'registration/register.html',{'form':form})    

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username') or None
        password = request.POST.get('password') or None
        if not password :
            messages.error(request, "Please enter password.")

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'registration/login.html')
        valid_em = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])"
     
        check_email_or_username = re.match(valid_em,username)
        print(check_email_or_username)
        if check_email_or_username:
             username_db = User.objects.get(email = username)
             user = authenticate(username=username_db,password=password)
        else:
             user = authenticate(username=username,password=password)
        if user:
            login(request,user)
            messages.success(request,"Logged in successfully :)")
            return redirect('home_page')
                
            
        else:
            messages.error(request, "Invalid Credentials")


    return render(request,'registration/login.html')

def logout_user(request):
    logout(request)
    return redirect('home_page')

def logpage(request):
    return redirect(request,'registration/login.html')    



