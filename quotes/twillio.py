# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = "f1eeaf025652410897a2bee8ba4a43b6"
client = Client(TWILIO_ACCOUNT_SID, auth_token)

call = client.calls.create(
  url="http://demo.twilio.com/docs/voice.xml",
  to="+40741755325",
  from_="+13159037163"
)

print(call.sid)