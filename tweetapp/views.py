from django.shortcuts import get_object_or_404, render,HttpResponse,redirect
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,authenticate,logout
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from .forms import UpdateProfileForm
import os
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import OuterRef, Subquery
# Create your views here.




# lets get file path

# def get_file_path(url):
#     file_path = os.path.join(settings.MEDIA_ROOT,url.name)

#     if file_path:
#         return file_path
#     else:
#         return None 


def home(request):
    if request.user.is_authenticated:
        saved_posts = SavedPosts.objects.filter(user = request.user)
        list_id_of_saved_posts=saved_posts.values_list('tweet_id',flat=True)
        tweets = Tweet.objects.all().order_by('-created_at')
        print(list_id_of_saved_posts)
        return render(request,'home.html',{'tweets':tweets or None,'list_id_of_saved_posts':list_id_of_saved_posts})
    else:
        return render(request,'home.html')
  


def profile_list(request):
    if request.user.is_authenticated:     
        profiles = Profile.objects.exclude(user=request.user)
        return render(request, 'profile_list.html', {"profiles": profiles})
    else:   
        messages.warning(request, "You must be logged into this Page ...")
        return redirect('home')


def profile(request,pk):
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile,user_id=pk)
        if profile:
            tweets = Tweet.objects.filter(user = profile.user).order_by('-created_at')

            return render(request,'profile.html',{'profile':profile,'tweets':tweets})
        else:
            return render(request,'notexists.html')

    else:
        messages.warning(request, "You must be logged into this Page ...")
        return redirect('home')

def follow_unfollow(request,id):
        profile_follow_unfollow = get_object_or_404(Profile,user_id=id)
        if request.method == "POST":
            current_user_profile  = request.user.profile
            action = request.POST.get('follow',None)
            if action=="unfollow":
                current_user_profile.follows.remove(profile_follow_unfollow)
                Notification.objects.create(
                    notify_by=current_user_profile,  
                    notified_user=profile_follow_unfollow,  
                    notify_type="unfollow"
                )
            else:
                current_user_profile.follows.add(profile_follow_unfollow) 
                Notification.objects.create(
                        notify_by=current_user_profile,  
                        notified_user=profile_follow_unfollow,  
                        notify_type="follow"
                    )
                
            current_user_profile.save()  
            return profile(request,id)
        return render(request,'profile.html')

# @login_required(login_url='/login/')     
def add_tweet(request):
    if request.user.is_authenticated:
        logged_user = request.user

        if request.method ==  "POST":
            tweet_title = request.POST.get('tweet_title') or None
            tweet_body = request.POST.get('body')  or None
            tweet_image = request.FILES.get('tweet_image')  or None

            new_tweet = Tweet()
            new_tweet.tweet_title = tweet_title
            new_tweet.body = tweet_body
            new_tweet.user = logged_user
            new_tweet.tweet_image = tweet_image
            
            new_tweet.save()
            messages.success(request, 'Your tweet has been posted! Successfully')
            return redirect('home')
    else:
        messages.success(request, "You must be logged into this Page to add a tweet ...")
        return redirect('home')


def delete_tweet(request,pk):
    tweet = get_object_or_404(Tweet,id=pk)
    tweet_image = tweet.tweet_image

    """
    You're able to skip manually checking the file path (tweet_image.path) 
    and whether the file exists (os.path.exists(tweet_image_path)) because Django takes care of that internally when you use delete().
    When you call tweet_image.delete(), Django's storage backend knows how to handle the file removal, whether it's stored locally 
    or in a cloud service, and the code is simplified.
    """
  

    # if tweet_image and tweet_image.path:
    #     print(tweet_image)
    #     tweet_image_path = tweet_image.path  -------> instead of this long process just use for image and filefiled is .delete() method

    #     if os.path.exists(tweet_image_path):
    #         print(tweet_image_path)
    #         os.remove(tweet_image_path)    
    
    if tweet_image:
        tweet_image.delete()

    tweet.delete()
    next_url = request.META.get("HTTP_REFERER")
    messages.success(request,"Tweet deleted successfully")
    return redirect (next_url)





def add_likes(request,id):
    tweet = get_object_or_404(Tweet,id=id)
    if tweet:
        like, created = TweetLikes.objects.get_or_create(user=request.user, tweet=tweet)
        print(f"Like created: {created}, Total Likes: {tweet.like_count()}") 
        # print(Notification.objects.all().values())
        if created:
            Notification.objects.create(
                notify_by=request.user.profile,
                notified_user=tweet.user.profile,
                notify_tweet=tweet,
                notify_type="like"
            )

        if not created:
            like.delete()  


        next_url = request.POST.get('next',None)
        print(f"Tweet: {tweet}, User: {request.user}")
        print(f"next_url: {next_url or None}, like: {like}, created: {created}")
        # if next_url: 
        #     return redirect('prof',pk=next_url) 

        # print(request.POST)
        # return redirect('home')    
        return redirect(request.META.get("HTTP_REFERER"))

def add_comments(request,id):
    tweet = get_object_or_404(Tweet,id=id)
    if tweet:
        if request.method == "POST":
            description = request.POST.get('description')
            TweetComment.objects.create(user=request.user,tweet=tweet,description = description) 
            Notification.objects.create(
                notify_by=request.user.profile,
                notified_user=tweet.user.profile,
                notify_tweet=tweet,
                notify_type="comment"
            )   

            print("Commented >>>")
            messages.success(request,"Comment added successfully !!!")
            # referer = request.META.get('HTTP_REFERER', 'home')
            next = request.POST.get('next','home')
            print(next)
            return redirect(next)
    else:
        messages.warning(request,"please login to add comments")
        return redirect('home')

def signin(request):
    if request.method == "POST":
        username = request.POST["username"] 
        password = request.POST["password"]
        user = authenticate(username=username,password=password)
        print(user)
        if user:
            login(request,user)
            messages.success(request,"Logged in Successfully")
            return redirect('home') 
        else:
            messages.error(request, "Invalid Credentials") 
            return redirect('signin')
    return render(request,'registration/login.html')    

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        username = request.POST.get("username")
        email = request.POST.get("email")
        username_exits = User.objects.filter(username=username).exists()
        phone_number = request.POST.get("full_phone_number")
        print(phone_number)

        if username_exits:
            messages.success(request,"User with this username already exists please try a unique username")
            return redirect('signup')
        exists_phone = Profile.objects.filter(phone_number = phone_number).exists()
        if exists_phone:
                messages.success(request,"This phone number is already registered")
                return redirect('signup')
        
        
        if form.is_valid():
            user = form.save()
            print(user)
            user.email = email  # Assign the email to the user instance
            user.save()
            profile = get_object_or_404(Profile,user = user)                    
            profile.phone_number = phone_number
            profile.save()

            messages.success(request,"User created successfully please login now")
            return redirect('signin')
    else:
        form = UserCreationForm()
    return render(request,'registration/register.html',{'form':form})    


def logout_user(request):
    logout(request)
    messages.success(request,"logged out successfully ")
    return redirect('home')

def search_user(request):
    if request.method == "GET":
        username = request.GET.get('username')
        username = User.objects.filter(username=username).first()
        if username:
            return profile(request,username.id)
        else:
            return render(request,"notexists.html")
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)  

@login_required(login_url='/login/') 
def suggest_users(request):
    query = request.GET.get('username', '')
    if len(query)>0:
        # Perform a case-insensitive search for usernames containing the query
        users = User.objects.filter(username__icontains=query).values('username')[:10]
        suggestions = list(users)  # Convert queryset to list
        return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)          


def update_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(Profile, user=user)

    if request.method == "POST" and "update" in request.POST:
        form = UpdateProfileForm(request.POST, request.FILES, instance=user_profile)
        print(request.FILES.get('image') or None,"\n",request.POST)
        if 'image-clear' in request.POST:  # 'image-clear' is the name of the checkbox field in the form so i could get to know that user want to delete previous file now want to upload any profile pic
            if user_profile.image:
                user_profile.image.delete() 

        new_profile_img = request.FILES.get('image')  # Get the uploaded file directly from request.FILES
        if new_profile_img and user_profile.image:
            user_profile.image.delete() 

        if form.is_valid():
            # print(form.cleaned_data)
            # new_profile_img = form.cleaned_data.get("image")
            # print(new_profile_img)
            # old_profile_image = user_profile.image
            # print(old_profile_image)
            form.save() 

            # if old_profile_image and new_profile_img and new_profile_img!=old_profile_image:
            #     old_profile_image_path = old_profile_image.path
            #     if default_storage.exists(old_profile_image_path):
            #         default_storage.delete(old_profile_image_path)   # instead of this log just use .delete(save=false) to ensure do not save just after image uploaded

            # if old_profile_image and new_profile_img and old_profile_image != new_profile_img:
            #     old_profile_image.delete()


            if form.errors:
                print(form.errors)
            messages.success(request, "Profile updated successfully!")
            return redirect('prof',pk=user.id)

    else:
        form = UpdateProfileForm(instance=user_profile)

    return render(request, 'update_profile.html', {'form': form})

@login_required(login_url='/login/') 
def add_Save_Post(request,id):
    tweet = get_object_or_404(Tweet,id=id)
    next_route_URL = request.META.get("HTTP_REFERER")

    if tweet:
        saved_posts,created = SavedPosts.objects.get_or_create(user=request.user , tweet=tweet)
        if not created:
            saved_posts.delete()
            messages.success(request,"Post Unsaved Successfully")
            return redirect (next_route_URL)

        messages.success(request,"Post Saved Successfully")
        return redirect (next_route_URL)
        
    else:
        messages.success(request,"Something went wrong")
        return redirect('home')
        
def saved_posts(request):
    saved_posts_for_users = SavedPosts.objects.filter(user=request.user)

    list_of_all_saved_posts = saved_posts_for_users.values_list('tweet_id',flat=True)
    tweets = Tweet.objects.filter(id__in=list_of_all_saved_posts).annotate(
        saved_at=Subquery(
            saved_posts_for_users.filter(tweet_id=OuterRef('id')).values('saved_at')[:1]
        )
    )
    print(tweets)
    
    
    print(list(list_of_all_saved_posts))
    return render(request,'saved_posts.html',{'tweets':tweets,'list_of_all_saved_posts':list_of_all_saved_posts}) 


# def saved_posts(request):
#     saved_posts_for_user = SavedPosts.objects.filter(user=request.user)
    
#     list_of_all_saved_posts = saved_posts_for_user.values_list('tweet_id', flat=True)

#     tweets = Tweet.objects.filter(id__in=list_of_all_saved_posts)

#     print(tweets)
#     print(list(list_of_all_saved_posts))

#     return render(request, 'saved_posts.html', {
#         'tweets': tweets,
#         'list_of_all_saved_posts': list_of_all_saved_posts
#     })



@login_required(login_url='/login/') 
def user_notifications(request):
    notifications = Notification.objects.filter(notified_user=request.user.profile,is_read=False).order_by('-notify_time')
    return render(request, "notifications.html", {"notifications": notifications})


@login_required(login_url='/login/')
def mark_as_read_notification(request,id):
    notification = Notification.objects.get(id=id)
    notification.is_read = True
    notification.save()

    return redirect('notification_list') 
