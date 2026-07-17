import firebase_admin
from firebase_admin import credentials, messaging

# 🔐 INIT FIREBASE ONLY ONCE
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")
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

    messaging.send(message)
