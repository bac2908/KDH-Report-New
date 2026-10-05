from .common import APIError, GOOGLE_ENV, register_secret, request_json, require_env


def get_google_access_token() -> str:
    _, body = request_json('POST', 'https://oauth2.googleapis.com/token', data={
        'client_id': require_env(GOOGLE_ENV[0]),
        'client_secret': require_env(GOOGLE_ENV[1]),
        'refresh_token': require_env(GOOGLE_ENV[2]),
        'grant_type': 'refresh_token',
    })
    token = body.get('access_token')
    if not isinstance(token, str) or not token:
        raise APIError('Google OAuth không trả access token hợp lệ.', 200)
    return register_secret(token)
