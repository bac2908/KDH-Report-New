import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


load_dotenv()


SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def main():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Thiếu GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET trong .env"
        )

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                "http://localhost"
            ],
        }
    }

    flow = InstalledAppFlow.from_client_config(
        client_config,
        SCOPES,
    )

    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    print("\nOAuth thành công.")
    print(
        "\nCopy giá trị Refresh Token dưới đây "
        "vào GOOGLE_REFRESH_TOKEN trong .env:\n"
    )

    print(credentials.refresh_token)


if __name__ == "__main__":
    main()