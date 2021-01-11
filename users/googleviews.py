from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2CallbackView,
                                                          OAuth2LoginView)

from google.auth.transport import requests
from google.oauth2 import id_token


class GoogleOAuth2AdapterIdToken(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        id_info = id_token.verify_oauth2_token( token.token, requests.Request(), app.client_id)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        extra_data = id_info
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login


oauth2_login = OAuth2LoginView.adapter_view(GoogleOAuth2AdapterIdToken)
oauth2_callback = OAuth2CallbackView.adapter_view(GoogleOAuth2AdapterIdToken)
