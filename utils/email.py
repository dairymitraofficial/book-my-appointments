import os
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)


def send_email(to, subject, body):
    print("➡️ send_email CALLED")

    sender = {
        "name": os.getenv("SENDER_NAME"),
        "email": os.getenv("SENDER_EMAIL")
    }

    email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,
        to=[{"email": to}],
        subject=subject,
        html_content=f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Book My Appointments</h2>

            <p>Hello,</p>

            <p>{body}</p>

            <p style="margin-top:20px;">
                This OTP is valid for <b>2 minutes</b>.
            </p>

            <hr>

            <p style="font-size:12px;color:gray;">
                If you didn't request this OTP, you can safely ignore this email.
            </p>
        </body>
        </html>
        """
    )

    try:
        api_instance.send_transac_email(email)
        print("✅ EMAIL SENT")
        return True

    except ApiException as e:
        print("❌ EMAIL ERROR:", e)
        return False

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return False