"""
Conditional decorators for free-tier compatibility.
"""
import os
from functools import wraps
from django_ratelimit.decorators import ratelimit


def conditional_ratelimit(key='ip', rate='5/m', method=None):
    """
    Apply rate limiting only when Redis is available.
    Falls back to no rate limiting on free tier (no Redis).
    """
    def decorator(view_func):
        # Only apply rate limiting if Redis is configured
        if os.getenv('REDIS_URL', ''):
            return ratelimit(key=key, rate=rate, method=method)(view_func)
        else:
            # Return undecorated function if Redis not available
            return view_func
    return decorator
