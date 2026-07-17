import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

if not firebase_admin._apps:

    if "FIREBASE_CREDENTIALS" in os.environ:
        # Render
        firebase_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
        cred = credentials.Certificate(firebase_json)

    else:
        # Local
        cred = credentials.Certificate("firebase_service_account.json")

    firebase_admin.initialize_app(cred)


def send_push(token, title, body, url="/"):
    message = messaging.Message(
        data={
            "title": title,
            "body": body,
            "url": url
        },
        token=token
    )

    messaging.send(message)