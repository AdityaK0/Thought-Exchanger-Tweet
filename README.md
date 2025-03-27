# Thought Exchanger Tweet

Thought Exchanger Tweet is a Django-based web application designed for users to share, search, and engage with tweets in an interactive and user-friendly environment. Built using the Model-View-Template (MVT) architecture, it includes robust authentication and social features.


## Features

- Secure user authentication (Login, Logout, Register, Forgot Password)
- Create, edit, and delete tweets
- Like and unlike tweets
- Notifications when someone comment or like on your tweet
- Notification when someone follows you 
- Comment on tweets
- Save and unsave tweets
- Follow and unfollow users
- Search for tweets and users
- Upload profile and tweet images
- Admin panel for content moderation

## Project Structure

```
tweet/
│── apnatweet/                 # Main app for tweets
│   ├── migrations/            # Database migrations
│   ├── templates/apnatweet/   # HTML templates for tweets
│   ├── admin.py               # Admin panel configuration
│   ├── apps.py                # App configuration
│   ├── forms.py               # Forms for user input
│   ├── models.py              # Database models
│   ├── urls.py                # URL routing
│   ├── views.py               # Views for handling requests
│   ├── __init__.py            # Package marker
│── media/tweet_thumbnail/      # Uploaded images
│── templates/registration/     # Authentication templates
│── tweet/
│   ├── settings.py            # Project settings
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI configuration
│   ├── asgi.py                # ASGI configuration
│   ├── __init__.py            # Package marker
│── db.sqlite3                  # SQLite database
│── manage.py                   # Django's CLI management script
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- Django 5+
- Virtual environment (optional but recommended)

### Steps to Run Locally

1. **Clone the repository**
   ```sh
   git clone <repo-url>
   cd tweet
   ```
2. **Create a virtual environment & activate it Optinal if u want u can else u can also download the dependencies in local too**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
4. **Apply database migrations**
   ```sh
   python manage.py migrate
   ```
5. **Run the development server**
   ```sh
   python manage.py runserver
   ```
6. **Access the app**
   Open `http://127.0.0.1:8000/` in your browser.



## API Endpoints & Routes

- `/` - Home page displaying all tweets
- `/profile_list/` - List of all user profiles
- `/profile/<int:pk>/` - User profile page with tweets
- `/follow_unfollow/<int:id>/` - Follow/unfollow a user
- `/add_tweet/` - Create a new tweet
- `/delete_tweet/<int:pk>/` - Delete a tweet
- `/add_likes/<int:id>/` - Like/unlike a tweet
- `/add_comments/<int:id>/` - Add a comment to a tweet
-  `/notification_list/` - List of all notifications
-  `/mark_as_read/<int:id>/` - Marks as Read Notification
- `/signin/` - User login
- `/register/` - User registration
- `/logout/` - User logout
- `/search_user/` - Search for users by username
- `/suggest_users/` - Get user suggestions based on input
- `/update_profile/<str:username>/` - Update user profile
- `/add_Save_Post/<int:id>/` - Save/unsave a tweet
- `/saved_posts/` - View saved posts


```


