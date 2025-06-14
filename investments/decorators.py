from django.shortcuts import redirect
from functools import wraps

def login_context_required(expected_context):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.session.get('login_context') != expected_context:
                return redirect('account_login')  # Or a "403" page
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
