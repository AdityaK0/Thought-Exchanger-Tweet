from django.contrib import admin
from django.contrib.auth.models import Group,User
from .models import *


admin.site.unregister(Group)   # to remove group table section from admin panel

# # Extend User Model  do this if u dont want to show extra fileds on the admin panel



# # Unregister intial User
admin.site.unregister(User)
# admin.site.register(Profile)  not needed because got merged with anothe table 

# Mix two tables

class ProfileInline(admin.StackedInline):
    model = Profile

class UserAdmin(admin.ModelAdmin):
    model = User
    fields = ["username","email"]
    inlines = [ProfileInline]    

admin.site.register(User,UserAdmin)    


# to modify the display items in admin panel else u can do it from model
class Tweets(admin.ModelAdmin):
    list_display = ["user","tweet_title","created_at"]
    search_fields = ["user","tweet_title","created_at"]




admin.site.register(Tweet,Tweets)
admin.site.register(TweetLikes)
admin.site.register(TweetComment)
admin.site.register(SavedPosts)
