from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15, 
        required=False, 
        label="Phone Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Save phone number to Profile
            phone_number = self.cleaned_data.get('phone_number')
            Profile.objects.create(user=user, phone_number=phone_number)
        return user
    
class UpdateProfileForm(forms.ModelForm):
    date_of_birth = forms.DateField(
    widget=forms.DateInput(attrs={'type': 'date'})
    )
    class Meta:
        model = Profile
        
        # choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
        # fullname = forms.CharField(max_length=300)
        # gender = forms.ChoiceField(choices=choices)
        # date_of_birth = forms.DateTimeInput()
        # bio = forms.CharField(max_length=300)

        fields = ["image","fullname","gender","date_of_birth","bio"]



# class NewUserRegistrationForm(forms.ModelForm):
#     class Meta:
#         model = Profile

#     pass
