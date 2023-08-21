from functools import wraps

from django.http import JsonResponse
from django.utils import timezone

from summarizer.auth_app.models import Account


def get_or_create_account(google_account_id, acc_email=None):
    usage_reset_date = timezone.now()
    print(f'from get or create - email {acc_email}')
    try:
        account = Account.objects.get(google_account_id=google_account_id)
    except Account.DoesNotExist:
        account = Account(google_account_id=google_account_id, email=acc_email, usage_reset_date=usage_reset_date)
        account.save()
    return account


def login_required_api(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Authentication required'}, status=401)

    return _wrapped_view
