# arena-account
Django project user account management for the ARENA.

**Dependencies**: `python3`, `pip3`, `virtualenv` (and `requirements.txt`; check if path in `Makefile` is correct)

## Production Setup
1. Setup a [Google Cloud App](https://developers.google.com/identity/protocols/oauth2) for your instance of the ARENA.
2. Make sure to set up [Google Web OAuth](https://developers.google.com/identity/protocols/oauth2/web-server) for the ARENA web client as well as [Google Limited-Input OAuth](https://developers.google.com/identity/protocols/oauth2/limited-input-device) for the ARENA Python client.
3. For the Google Web OAuth Credentials you will need to add Authorized JavaScript origins:
    ```
    http://your.domain
    http://localhost:8989
    ```
4. For the Google Web OAuth Credentials you will need to add Authorized redirect URIs:
    ```
    http://your.domain/user/accounts/google/login/callback/
    http://localhost:8989/
    ```

## Local Development Setup
1. For the Google Web OAuth Credentials you will need to add Authorized JavaScript origins:
    ```
    http://localhost:8000
    ```
2. For the Google Web OAuth Credentials you will need to add Authorized redirect URIs:
    ```
    http://localhost:8000/user/accounts/google/login/callback/
    ```
3. Create an environment file, `.env`, for testing on localhost using your Google auth app "Client id" and "Secret key".
```env
HOSTNAME=localhost
ARENA_REALM=realm
EMAIL=nouser@nomail.com
GAUTH_CLIENTID=Google_OAuth_Web_application_Client_ID
GAUTH_CLIENTSECRET=Google_OAuth_Web_application_Client_Secret
GAUTH_INSTALLED_CLIENTID=Google_OAuth_Desktop_Client_ID
GAUTH_INSTALLED_CLIENTSECRET=Google_OAuth_Desktop_Client_Secret
GAUTH_DEVICE_CLIENTID=Google_OAuth_TV_and_Limited_Input_Client_ID
GAUTH_DEVICE_CLIENTSECRET=Google_OAuth_TV_and_Limited_Input_Client_Secret
MQTT_TOKEN_PRIVKEY=/path/to/your/test/key/file.pem
```
4. Create db: ```make migrate```
5. Create admin user: ```python3 manage.py createsuperuser --email admin@example.com --username admin```

### Execute
- ```make run```

### UIs
- Admin: `http://localhost:8000/user/admin`
- Main Page: `http://localhost:8000/user`
