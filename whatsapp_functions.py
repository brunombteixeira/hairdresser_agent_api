import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

def send_custom_message(content: str, recipient: str):
    url = f"https://graph.facebook.com/{os.getenv("VERSION")}/{os.getenv("PHONE_NUMBER_ID")}/messages"
    headers = (
        {
            "Content-type":"application/json",
            "Authorization": f"Bearer {os.getenv("ACCESS_TOKEN")}"
        }
    )
    data = ({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{recipient}",
        "type": "text",
        "text": { "preview_url": False, "body": content }
    })

    response = requests.post(url, data=json.dumps(data), headers=headers)

    print(response.status_code)
    print(response.json())
    print("Message sent successfully")
