import os
import re
import uuid
import hashlib
import logging
import random
import string
import typing
import decimal
import datetime
import functools
import itertools
import collections

from typing import (
    Any, Dict, List, Union, Optional, Callable, 
    Type, TypeVar, Tuple, Generator
)

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify

# Configure logging
logger = logging.getLogger(__name__)

# Custom type hints
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=Model)

class ValidationError(Exception):
    """Custom validation error for utility functions."""
    pass

def generate_unique_slug(
    model_class: Type[ModelType], 
    value: str, 
    slug_field: str = 'slug', 
    max_length: int = 50
) -> str:
    """
    Generate a unique slug for a given model and value.
    
    Args:
        model_class (Type[Model]): Django model class
        value (str): Original value to slugify
        slug_field (str, optional): Field name for slug. Defaults to 'slug'.
        max_length (int, optional): Maximum slug length. Defaults to 50.
    
    Returns:
        str: Unique slug
    """
    original_slug = slugify(value)[:max_length]
    unique_slug = original_slug
    counter = 1
    
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        suffix = f'-{counter}'
        unique_slug = f"{original_slug[:max_length-len(suffix)]}{suffix}"
        counter += 1
    
    return unique_slug

def send_templated_email(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    recipient_list: List[str],
    from_email: Optional[str] = None
) -> int:
    """
    Send an email using a Django template.
    
    Args:
        subject (str): Email subject
        template_name (str): Template path
        context (Dict): Context for template rendering
        recipient_list (List[str]): List of recipient emails
        from_email (Optional[str]): Sender email
    
    Returns:
        int: Number of emails sent
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        email_content = render_to_string(template_name, context)
        return send_mail(
            subject, 
            email_content, 
            from_email, 
            recipient_list, 
            html_message=email_content
        )
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return 0

def retry(
    max_attempts: int = 3, 
    delay: int = 1, 
    backoff: int = 2, 
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts (int): Maximum retry attempts
        delay (int): Initial delay between retries
        backoff (int): Backoff multiplier
        exceptions (Tuple): Exceptions to catch and retry
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    
                    logger.warning(f"Retry attempt {attempts}: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator

def bulk_create_with_batch(
    model_class: Type[ModelType], 
    objects: List[ModelType], 
    batch_size: int = 1000
) -> List[ModelType]:
    """
    Bulk create objects in batches to handle large datasets.
    
    Args:
        model_class (Type[Model]): Django model class
        objects (List[Model]): List of model instances to create
        batch_size (int, optional): Number of objects per batch
    
    Returns:
        List[Model]: Created model instances
    """
    created_objects = []
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i+batch_size]
        created_objects.extend(model_class.objects.bulk_create(batch))
    
    return created_objects

def generate_random_password(
    length: int = 12, 
    include_uppercase: bool = True, 
    include_lowercase: bool = True,
    include_digits: bool = True, 
    include_special_chars: bool = True
) -> str:
    """
    Generate a random password with specified complexity.
    
    Args:
        length (int): Password length
        include_uppercase (bool): Include uppercase letters
        include_lowercase (bool): Include lowercase letters
        include_digits (bool): Include digits
        include_special_chars (bool): Include special characters
    
    Returns:
        str: Generated password
    """
    character_sets = []
    
    if include_uppercase:
        character_sets.append(string.ascii_uppercase)
    if include_lowercase:
        character_sets.append(string.ascii_lowercase)
    if include_digits:
        character_sets.append(string.digits)
    if include_special_chars:
        character_sets.append('!@#$%^&*()_+-=[]{}|;:,.<>?')
    
    if not character_sets:
        raise ValueError("At least one character set must be included")
    
    all_characters = ''.join(character_sets)
    password = ''.join(random.choice(all_characters) for _ in range(length))
    
    return password

def validate_data(
    data: Dict[str, Any], 
    rules: Dict[str, Callable[[Any], bool]]
) -> Dict[str, str]:
    """
    Validate data against a set of validation rules.
    
    Args:
        data (Dict): Data to validate
        rules (Dict): Validation rules mapping key to validation function
    
    Returns:
        Dict: Validation errors
    """
    errors = {}
    
    for key, rule in rules.items():
        try:
            if key not in data or not rule(data[key]):
                errors[key] = f"Invalid value for {key}"
        except Exception as e:
            errors[key] = str(e)
    
    return errors

def cache_function(
    timeout: int = 300, 
    key_prefix: str = 'function_cache_'
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

def paginate_queryset(
    queryset: QuerySet, 
    page: int = 1, 
    per_page: int = 10
) -> Dict[str, Any]:
    """
    Paginate a Django QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet to paginate
        page (int): Current page number
        per_page (int): Items per page
    
    Returns:
        Dict: Pagination metadata and paginated results
    """
    total_items = queryset.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_queryset = queryset[start_index:end_index]
    
    return {
        'total_items': total_items,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'results': list(paginated_queryset)
    }

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename (str): Original filename
        max_length (int): Maximum filename length
    
    Returns:
        str: Sanitized filename
    """
    # Remove invalid filesystem characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Truncate filename
    filename = filename[:max_length]
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    return filename

def humanize_timedelta(delta: datetime.timedelta) -> str:
    """
    Convert timedelta to human-readable string.
    
    Args:
        delta (timedelta): Time difference
    
    Returns:
        str: Human-readable time difference
    """
    days = delta.days
    seconds = delta.seconds
    
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    
    return ', '.join(parts) if parts else '0 seconds'

# Advanced decorators and context managers
class atomic_transaction:
    """
    Context manager for database transactions.
    Ensures atomic database operations with optional save points.
    """
    def __init__(self, using=None, savepoint=True):
        self.using = using
        self.savepoint = savepoint
    
    def __enter__(self):
        self.transaction = transaction.atomic(using=self.using, savepoint=self.savepoint)
        return self.transaction.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.transaction.__exit__(exc_type, exc_val, exc_tb)

def throttle(
    max_calls: int = 10, 
    period: int = 60,
    method_key: Optional[Callable[[Any], str]] = None
) -> Callable:
    """
    Decorator to throttle function calls.
    
    Args:
        max_calls (int): Maximum calls allowed
        period (int): Time period in seconds
        method_key (Optional[Callable]): Function to generate unique key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        calls = collections.defaultdict(list)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = method_key(*args, **kwargs) if method_key else 'default'
            current_time = time.time()
            
            # Remove old calls
            calls[key] = [t for t in calls[key] if current_time - t < period]
            
            if len(calls[key]) >= max_calls:
                raise RuntimeError(f"Too many calls for {key}. Rate limit exceeded.")
            
            calls[key].append(current_time)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def generate_unique_filename(
    instance: ModelType, 
    filename: str, 
    upload_to: str = 'uploads/'
) -> str:
    """
    Generate a unique filename for file uploads.
    
    Args:
        instance (Model): Model instance
        filename (str): Original filename
        upload_to (str): Upload directory
    
    Returns:
        str: Unique filename path
    """
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(upload_to, unique_filename)

def log_performance(
    logger: logging.Logger = logger, 
    level: int = logging.INFO
) -> Callable:
    """
    Decorator to log function performance metrics.
    
    Args:
        logger (Logger): Logger to use
        level (int): Logging level
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger.log(
                level, 
                f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds"
            )
            return result
        return wrapper
    return decorator

# Add more utility functions as needed...

# Remember to import additional required libraries at the top of the file
import time

import os
import re
import uuid
import hashlib
import logging
import random
import string
import typing
import decimal
import datetime
import functools
import itertools
import collections

from typing import (
    Any, Dict, List, Union, Optional, Callable, 
    Type, TypeVar, Tuple, Generator
)

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify

# Configure logging
logger = logging.getLogger(__name__)

# Custom type hints
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=Model)

class ValidationError(Exception):
    """Custom validation error for utility functions."""
    pass

def generate_unique_slug(
    model_class: Type[ModelType], 
    value: str, 
    slug_field: str = 'slug', 
    max_length: int = 50
) -> str:
    """
    Generate a unique slug for a given model and value.
    
    Args:
        model_class (Type[Model]): Django model class
        value (str): Original value to slugify
        slug_field (str, optional): Field name for slug. Defaults to 'slug'.
        max_length (int, optional): Maximum slug length. Defaults to 50.
    
    Returns:
        str: Unique slug
    """
    original_slug = slugify(value)[:max_length]
    unique_slug = original_slug
    counter = 1
    
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        suffix = f'-{counter}'
        unique_slug = f"{original_slug[:max_length-len(suffix)]}{suffix}"
        counter += 1
    
    return unique_slug

def send_templated_email(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    recipient_list: List[str],
    from_email: Optional[str] = None
) -> int:
    """
    Send an email using a Django template.
    
    Args:
        subject (str): Email subject
        template_name (str): Template path
        context (Dict): Context for template rendering
        recipient_list (List[str]): List of recipient emails
        from_email (Optional[str]): Sender email
    
    Returns:
        int: Number of emails sent
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        email_content = render_to_string(template_name, context)
        return send_mail(
            subject, 
            email_content, 
            from_email, 
            recipient_list, 
            html_message=email_content
        )
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return 0

def retry(
    max_attempts: int = 3, 
    delay: int = 1, 
    backoff: int = 2, 
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts (int): Maximum retry attempts
        delay (int): Initial delay between retries
        backoff (int): Backoff multiplier
        exceptions (Tuple): Exceptions to catch and retry
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    
                    logger.warning(f"Retry attempt {attempts}: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator

def bulk_create_with_batch(
    model_class: Type[ModelType], 
    objects: List[ModelType], 
    batch_size: int = 1000
) -> List[ModelType]:
    """
    Bulk create objects in batches to handle large datasets.
    
    Args:
        model_class (Type[Model]): Django model class
        objects (List[Model]): List of model instances to create
        batch_size (int, optional): Number of objects per batch
    
    Returns:
        List[Model]: Created model instances
    """
    created_objects = []
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i+batch_size]
        created_objects.extend(model_class.objects.bulk_create(batch))
    
    return created_objects

def generate_random_password(
    length: int = 12, 
    include_uppercase: bool = True, 
    include_lowercase: bool = True,
    include_digits: bool = True, 
    include_special_chars: bool = True
) -> str:
    """
    Generate a random password with specified complexity.
    
    Args:
        length (int): Password length
        include_uppercase (bool): Include uppercase letters
        include_lowercase (bool): Include lowercase letters
        include_digits (bool): Include digits
        include_special_chars (bool): Include special characters
    
    Returns:
        str: Generated password
    """
    character_sets = []
    
    if include_uppercase:
        character_sets.append(string.ascii_uppercase)
    if include_lowercase:
        character_sets.append(string.ascii_lowercase)
    if include_digits:
        character_sets.append(string.digits)
    if include_special_chars:
        character_sets.append('!@#$%^&*()_+-=[]{}|;:,.<>?')
    
    if not character_sets:
        raise ValueError("At least one character set must be included")
    
    all_characters = ''.join(character_sets)
    password = ''.join(random.choice(all_characters) for _ in range(length))
    
    return password

def validate_data(
    data: Dict[str, Any], 
    rules: Dict[str, Callable[[Any], bool]]
) -> Dict[str, str]:
    """
    Validate data against a set of validation rules.
    
    Args:
        data (Dict): Data to validate
        rules (Dict): Validation rules mapping key to validation function
    
    Returns:
        Dict: Validation errors
    """
    errors = {}
    
    for key, rule in rules.items():
        try:
            if key not in data or not rule(data[key]):
                errors[key] = f"Invalid value for {key}"
        except Exception as e:
            errors[key] = str(e)
    
    return errors

def cache_function(
    timeout: int = 300, 
    key_prefix: str = 'function_cache_'
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

def paginate_queryset(
    queryset: QuerySet, 
    page: int = 1, 
    per_page: int = 10
) -> Dict[str, Any]:
    """
    Paginate a Django QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet to paginate
        page (int): Current page number
        per_page (int): Items per page
    
    Returns:
        Dict: Pagination metadata and paginated results
    """
    total_items = queryset.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_queryset = queryset[start_index:end_index]
    
    return {
        'total_items': total_items,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'results': list(paginated_queryset)
    }

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename (str): Original filename
        max_length (int): Maximum filename length
    
    Returns:
        str: Sanitized filename
    """
    # Remove invalid filesystem characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Truncate filename
    filename = filename[:max_length]
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    return filename

def humanize_timedelta(delta: datetime.timedelta) -> str:
    """
    Convert timedelta to human-readable string.
    
    Args:
        delta (timedelta): Time difference
    
    Returns:
        str: Human-readable time difference
    """
    days = delta.days
    seconds = delta.seconds
    
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    
    return ', '.join(parts) if parts else '0 seconds'

# Advanced decorators and context managers
class atomic_transaction:
    """
    Context manager for database transactions.
    Ensures atomic database operations with optional save points.
    """
    def __init__(self, using=None, savepoint=True):
        self.using = using
        self.savepoint = savepoint
    
    def __enter__(self):
        self.transaction = transaction.atomic(using=self.using, savepoint=self.savepoint)
        return self.transaction.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.transaction.__exit__(exc_type, exc_val, exc_tb)

def throttle(
    max_calls: int = 10, 
    period: int = 60,
    method_key: Optional[Callable[[Any], str]] = None
) -> Callable:
    """
    Decorator to throttle function calls.
    
    Args:
        max_calls (int): Maximum calls allowed
        period (int): Time period in seconds
        method_key (Optional[Callable]): Function to generate unique key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        calls = collections.defaultdict(list)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = method_key(*args, **kwargs) if method_key else 'default'
            current_time = time.time()
            
            # Remove old calls
            calls[key] = [t for t in calls[key] if current_time - t < period]
            
            if len(calls[key]) >= max_calls:
                raise RuntimeError(f"Too many calls for {key}. Rate limit exceeded.")
            
            calls[key].append(current_time)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def generate_unique_filename(
    instance: ModelType, 
    filename: str, 
    upload_to: str = 'uploads/'
) -> str:
    """
    Generate a unique filename for file uploads.
    
    Args:
        instance (Model): Model instance
        filename (str): Original filename
        upload_to (str): Upload directory
    
    Returns:
        str: Unique filename path
    """
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(upload_to, unique_filename)

def log_performance(
    logger: logging.Logger = logger, 
    level: int = logging.INFO
) -> Callable:
    """
    Decorator to log function performance metrics.
    
    Args:
        logger (Logger): Logger to use
        level (int): Logging level
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger.log(
                level, 
                f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds"
            )
            return result
        return wrapper
    return decorator

# Add more utility functions as needed...

# Remember to import additional required libraries at the top of the file
import time

import os
import re
import uuid
import hashlib
import logging
import random
import string
import typing
import decimal
import datetime
import functools
import itertools
import collections

from typing import (
    Any, Dict, List, Union, Optional, Callable, 
    Type, TypeVar, Tuple, Generator
)

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify

# Configure logging
logger = logging.getLogger(__name__)

# Custom type hints
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=Model)

class ValidationError(Exception):
    """Custom validation error for utility functions."""
    pass

def generate_unique_slug(
    model_class: Type[ModelType], 
    value: str, 
    slug_field: str = 'slug', 
    max_length: int = 50
) -> str:
    """
    Generate a unique slug for a given model and value.
    
    Args:
        model_class (Type[Model]): Django model class
        value (str): Original value to slugify
        slug_field (str, optional): Field name for slug. Defaults to 'slug'.
        max_length (int, optional): Maximum slug length. Defaults to 50.
    
    Returns:
        str: Unique slug
    """
    original_slug = slugify(value)[:max_length]
    unique_slug = original_slug
    counter = 1
    
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        suffix = f'-{counter}'
        unique_slug = f"{original_slug[:max_length-len(suffix)]}{suffix}"
        counter += 1
    
    return unique_slug

def send_templated_email(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    recipient_list: List[str],
    from_email: Optional[str] = None
) -> int:
    """
    Send an email using a Django template.
    
    Args:
        subject (str): Email subject
        template_name (str): Template path
        context (Dict): Context for template rendering
        recipient_list (List[str]): List of recipient emails
        from_email (Optional[str]): Sender email
    
    Returns:
        int: Number of emails sent
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        email_content = render_to_string(template_name, context)
        return send_mail(
            subject, 
            email_content, 
            from_email, 
            recipient_list, 
            html_message=email_content
        )
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return 0

def retry(
    max_attempts: int = 3, 
    delay: int = 1, 
    backoff: int = 2, 
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts (int): Maximum retry attempts
        delay (int): Initial delay between retries
        backoff (int): Backoff multiplier
        exceptions (Tuple): Exceptions to catch and retry
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    
                    logger.warning(f"Retry attempt {attempts}: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator

def bulk_create_with_batch(
    model_class: Type[ModelType], 
    objects: List[ModelType], 
    batch_size: int = 1000
) -> List[ModelType]:
    """
    Bulk create objects in batches to handle large datasets.
    
    Args:
        model_class (Type[Model]): Django model class
        objects (List[Model]): List of model instances to create
        batch_size (int, optional): Number of objects per batch
    
    Returns:
        List[Model]: Created model instances
    """
    created_objects = []
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i+batch_size]
        created_objects.extend(model_class.objects.bulk_create(batch))
    
    return created_objects

def generate_random_password(
    length: int = 12, 
    include_uppercase: bool = True, 
    include_lowercase: bool = True,
    include_digits: bool = True, 
    include_special_chars: bool = True
) -> str:
    """
    Generate a random password with specified complexity.
    
    Args:
        length (int): Password length
        include_uppercase (bool): Include uppercase letters
        include_lowercase (bool): Include lowercase letters
        include_digits (bool): Include digits
        include_special_chars (bool): Include special characters
    
    Returns:
        str: Generated password
    """
    character_sets = []
    
    if include_uppercase:
        character_sets.append(string.ascii_uppercase)
    if include_lowercase:
        character_sets.append(string.ascii_lowercase)
    if include_digits:
        character_sets.append(string.digits)
    if include_special_chars:
        character_sets.append('!@#$%^&*()_+-=[]{}|;:,.<>?')
    
    if not character_sets:
        raise ValueError("At least one character set must be included")
    
    all_characters = ''.join(character_sets)
    password = ''.join(random.choice(all_characters) for _ in range(length))
    
    return password

def validate_data(
    data: Dict[str, Any], 
    rules: Dict[str, Callable[[Any], bool]]
) -> Dict[str, str]:
    """
    Validate data against a set of validation rules.
    
    Args:
        data (Dict): Data to validate
        rules (Dict): Validation rules mapping key to validation function
    
    Returns:
        Dict: Validation errors
    """
    errors = {}
    
    for key, rule in rules.items():
        try:
            if key not in data or not rule(data[key]):
                errors[key] = f"Invalid value for {key}"
        except Exception as e:
            errors[key] = str(e)
    
    return errors

def cache_function(
    timeout: int = 300, 
    key_prefix: str = 'function_cache_'
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

def paginate_queryset(
    queryset: QuerySet, 
    page: int = 1, 
    per_page: int = 10
) -> Dict[str, Any]:
    """
    Paginate a Django QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet to paginate
        page (int): Current page number
        per_page (int): Items per page
    
    Returns:
        Dict: Pagination metadata and paginated results
    """
    total_items = queryset.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_queryset = queryset[start_index:end_index]
    
    return {
        'total_items': total_items,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'results': list(paginated_queryset)
    }

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename (str): Original filename
        max_length (int): Maximum filename length
    
    Returns:
        str: Sanitized filename
    """
    # Remove invalid filesystem characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Truncate filename
    filename = filename[:max_length]
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    return filename

def humanize_timedelta(delta: datetime.timedelta) -> str:
    """
    Convert timedelta to human-readable string.
    
    Args:
        delta (timedelta): Time difference
    
    Returns:
        str: Human-readable time difference
    """
    days = delta.days
    seconds = delta.seconds
    
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    
    return ', '.join(parts) if parts else '0 seconds'

# Advanced decorators and context managers
class atomic_transaction:
    """
    Context manager for database transactions.
    Ensures atomic database operations with optional save points.
    """
    def __init__(self, using=None, savepoint=True):
        self.using = using
        self.savepoint = savepoint
    
    def __enter__(self):
        self.transaction = transaction.atomic(using=self.using, savepoint=self.savepoint)
        return self.transaction.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.transaction.__exit__(exc_type, exc_val, exc_tb)

def throttle(
    max_calls: int = 10, 
    period: int = 60,
    method_key: Optional[Callable[[Any], str]] = None
) -> Callable:
    """
    Decorator to throttle function calls.
    
    Args:
        max_calls (int): Maximum calls allowed
        period (int): Time period in seconds
        method_key (Optional[Callable]): Function to generate unique key
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        calls = collections.defaultdict(list)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = method_key(*args, **kwargs) if method_key else 'default'
            current_time = time.time()
            
            # Remove old calls
            calls[key] = [t for t in calls[key] if current_time - t < period]
            
            if len(calls[key]) >= max_calls:
                raise RuntimeError(f"Too many calls for {key}. Rate limit exceeded.")
            
            calls[key].append(current_time)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def generate_unique_filename(
    instance: ModelType, 
    filename: str, 
    upload_to: str = 'uploads/'
) -> str:
    """
    Generate a unique filename for file uploads.
    
    Args:
        instance (Model): Model instance
        filename (str): Original filename
        upload_to (str): Upload directory
    
    Returns:
        str: Unique filename path
    """
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(upload_to, unique_filename)

def log_performance(
    logger: logging.Logger = logger, 
    level: int = logging.INFO
) -> Callable:
    """
    Decorator to log function performance metrics.
    
    Args:
        logger (Logger): Logger to use
        level (int): Logging level
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger.log(
                level, 
                f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds"
            )
            return result
        return wrapper
    return decorator

# Add more utility functions as needed...

# Remember to import additional required libraries at the top of the file
import time