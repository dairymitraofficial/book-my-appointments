import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase only once
if not firebase_admin._apps:
    firebase_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(firebase_json)
    firebase_admin.initialize_app(cred)


def send_push(token, title, body, url="/"):
    """
    DATA-ONLY PUSH
    Notification UI will be handled by Service Worker
    """

    message = messaging.Message(
        data={
            "title": title,
            "body": body,
            "url": url
        },
        token=token
    )

    messaging.send(message)git add .