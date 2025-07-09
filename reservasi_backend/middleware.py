from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

User = get_user_model()

class AppAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Jangan ubah request.user untuk URL admin
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Jika ada sesi aplikasi, atur request.user berdasarkan app_auth
        if 'app_auth' in request.session and 'user_id' in request.session['app_auth']:
            try:
                user = User.objects.get(id=request.session['app_auth']['user_id'])
                request.user = user
            except User.DoesNotExist:
                request.user = AnonymousUser()
                if 'app_auth' in request.session:
                    del request.session['app_auth']
        else:
            # Jika tidak ada sesi aplikasi, pastikan request.user adalah AnonymousUser
            request.user = AnonymousUser()

        response = self.get_response(request)
        return response