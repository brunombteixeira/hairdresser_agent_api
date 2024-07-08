import os
# from dotenv import load_dotenv
from supabase import create_client, Client

# load_dotenv()

url: str = "https://miquuhqxuttacqjfeodh.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1pcXV1aHF4dXR0YWNxamZlb2RoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjAzOTI5NjAsImV4cCI6MjAzNTk2ODk2MH0.GBUaCJGxd8d0oRo0qIvBls6v_6zZUq--QsATjA7DYpo"

supabase: Client = create_client(url, key)

# user = supabase.auth.sign_in_with_password({ "email": "brunombteixeira@gmail.com", "password": "thisisatestuser" })

def supa_insert_data(user_waid: str, message: str, created_by: str):
    try:
        response = (
            supabase.table("chat_history")
            .insert({"message": message, "user_waid": user_waid, "created_by": created_by})
            .execute()
        )
        print(f"Record added: {response}")
    except Exception as error:
        print("An exception occurred:", error)

def supa_fetch_data(user_waid: str):
    try:
        response = (
            supabase.table("chat_history")
            .select("*")
            .eq("user_waid",user_waid)
            .order("created_at")
            .limit(20)
            .execute()
        )
        chat_history = [message["message"] for message in response.data]
        return chat_history
    except Exception as error:
        print("An exception occurred:", error)
        return []
