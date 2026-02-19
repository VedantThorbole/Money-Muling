"""
Utils package initialization.
Exports all utility functions and classes for use throughout the application.
"""

from .csv_parser import CSVParser
from .json_formatter import JSONFormatter
from .validators import Validator

# Package metadata
__version__ = '1.0.0'
__author__ = 'RIFT 2026 Team'

# Utility functions that don't belong to specific classes
def format_timestamp(timestamp):
    """Format timestamp consistently across the application"""
    if hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return str(timestamp)

def safe_float_convert(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_convert(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def truncate_string(s, max_length=50, suffix='...'):
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_percentage(part, whole):
    """Calculate percentage safely"""
    if whole == 0:
        return 0.0
    return (part / whole) * 100

def group_by_key(items, key_func):
    """Group items by key function"""
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups

def merge_dicts(dict1, dict2, strategy='overwrite'):
    """Merge two dictionaries with specified strategy"""
    result = dict1.copy()
    
    if strategy == 'overwrite':
        result.update(dict2)
    elif strategy == 'sum':
        for key, value in dict2.items():
            if key in result:
                result[key] = result[key] + value
            else:
                result[key] = value
    elif strategy == 'average':
        for key, value in dict2.items():
            if key in result:
                result[key] = (result[key] + value) / 2
            else:
                result[key] = value
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")
    
    return result

def chunk_list(lst, chunk_size):
    """Split list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def remove_duplicates(lst, key_func=None):
    """Remove duplicates from list, optionally using key function"""
    if key_func is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    for item in lst:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def parse_bool(value):
    """Parse boolean from various formats"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'y', 'on')
    return False

def get_file_extension(filename):
    """Get file extension from filename"""
    if '.' not in filename:
        return ''
    return filename.split('.')[-1].lower()

def generate_id(prefix='', length=8):
    """Generate random ID with optional prefix"""
    import uuid
    random_part = uuid.uuid4().hex[:length]
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d, sep='.'):
    """Unflatten dictionary"""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        dct = result
        for part in parts[:-1]:
            if part not in dct:
                dct[part] = {}
            dct = dct[part]
        dct[parts[-1]] = value
    return result

def safe_divide(numerator, denominator, default=0.0):
    """Safe division with default value"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def format_currency(amount, currency='USD', symbol=True):
    """Format amount as currency"""
    if symbol:
        symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹'}
        return f"{symbols.get(currency, '$')}{amount:,.2f}"
    return f"{amount:,.2f} {currency}"

def time_it(func):
    """Decorator to measure function execution time"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

def singleton(cls):
    """Singleton decorator"""
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

# Export all utility functions
__all__ = [
    'CSVParser',
    'JSONFormatter',
    'Validator',
    'format_timestamp',
    'safe_float_convert',
    'safe_int_convert',
    'truncate_string',
    'validate_email',
    'calculate_percentage',
    'group_by_key',
    'merge_dicts',
    'chunk_list',
    'remove_duplicates',
    'parse_bool',
    'get_file_extension',
    'generate_id',
    'flatten_dict',
    'unflatten_dict',
    'safe_divide',
    'format_currency',
    'time_it',
    'singleton'
]