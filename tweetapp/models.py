from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime 
from phonenumber_field.modelfields import PhoneNumberField
# Create your models here.



class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    follows = models.ManyToManyField("self",related_name='followed_by',symmetrical=False,blank=True)
    updated = models.DateTimeField(User,auto_now=True)
    fullname = models.CharField(max_length=300,null=True,blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    image  = models.ImageField(upload_to='profile_image',null=True,blank=True)
    bio = models.TextField(null=True, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True, help_text='Enter phone number with country code.')

    def __str__(self) -> str:
        return self.user.username


class VerifyOtp(models.Model):
    otp = models.CharField(max_length=6)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.otp} - {self.generated_at}"
    


# create profile when new user signs up
@receiver(post_save, sender=User)
def create_profile(sender,instance,created,**kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()

        # need show user post to itself so follow it self
        user_profile.follows.set([instance.profile.id])
        user_profile.save()  # 2 times save because 1st to create the profile then follow himself 

# post_save.connect(create_profile,sender=User)


class Tweet(models.Model):
    user = models.ForeignKey(User,related_name='tweets',on_delete=models.DO_NOTHING)
    tweet_title = models.CharField(max_length=35)
    tweet_image = models.ImageField(upload_to='tweet_images',null=True,blank=True)
    body = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.tweet_title} - {self.created_at:%d-%m-%Y : %H:%M}"
    
    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count() 
    
class TweetLikes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet,related_name='likes',on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user','tweet')

    def __str__(self) -> str:
        return f"{self.tweet} - Likes {self.user}"

class TweetComment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet,related_name='comments',on_delete=models.CASCADE)
    description = models.CharField(max_length=400)
    comment_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tweet} - {self.description}"
    

    
class SavedPosts(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet,on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

