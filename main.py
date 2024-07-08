import os
from agent import create_agent
from whatsapp_functions import send_custom_message
from supabase_functions import supa_fetch_data, supa_insert_data
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
# from vectordb_functions import get_relevant_chat_history, store_chat_history

import logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/webhook")
async def handle_webhook(request: Request):
    logging.debug(f"Received webhook request: {request.query_params}")
    if request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        challenge = request.query_params.get("hub.challenge")
        logging.debug(f"Verification successful. Returning challenge: {challenge}")
        return PlainTextResponse(challenge)
    logging.warning("Verification failed")
    return "Error"

@app.post("/webhook")
async def handle_webhook_post(request: Request):
    """
    Process the incoming messages.
    """
    print("NEW MESSAGE RECEIVED!!!!")
    data = await request.json()

    if 'statuses' in data['entry'][0]['changes'][0]['value']:
        print("Object has a status")
    else:
        print(data)
        user_waid = data['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
        text_message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        print(f"TEXT MESSAGE: {text_message}")
        if text_message:
            supa_insert_data(message=text_message, user_waid=user_waid, created_by="user")
            chat_history = supa_fetch_data(user_waid)
            print(f"Chat history: {chat_history}")
            agent = create_agent()
            inputs = {"input": text_message, "chat_history": chat_history, "user_waid": user_waid}
            output = agent.invoke(inputs, config = {"configurable": {"thread_id": 1}})
            send_custom_message(output.get("agent_outcome").return_values['output'],user_waid)
            supa_insert_data(user_waid, output.get("agent_outcome").return_values['output'], "system")

    return {"status": "ok"}
