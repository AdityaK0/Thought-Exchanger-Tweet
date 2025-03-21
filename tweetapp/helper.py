import random
import http.client
import json

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(phone_number):
    auth_key = "436429AYeyXymwqw675bd9f3P1"  # Replace with your actual authentication key
    sender = "ADITYA1X"   # Replace with your actual sender ID
    otp = generate_otp()          # Generate OTP dynamically here
    message = f"Your OTP is {otp}"  # Customize the message

    conn = http.client.HTTPSConnection("control.msg91.com")
    headers = {
        "authkey": auth_key,
        "accept": "application/json",
        "content-type": "application/json",
    }

    # Ensure all values are JSON-serializable
    payload = {
        # "template_id": "YourTemplateID",  # Replace with your actual template ID
        "mobiles": str(phone_number),
        "message": message,
        "sender": sender,
        "otp": otp,
    }

    # Debug the payload
    print("Sending payload:", payload)

    conn.request("POST", "/api/v5/otp", body=json.dumps(payload), headers=headers)
    res = conn.getresponse()
    data = res.read()

    if res.status == 200:
        return otp  # Return OTP to store it temporarily
    else:
        raise Exception(f"Failed to send OTP. Response: {data.decode('utf-8')}")
