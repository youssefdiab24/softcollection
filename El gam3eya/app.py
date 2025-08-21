import os
import random
from dotenv import load_dotenv
from prompt import PROMPT
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import google
from livekit.plugins.turn_detector import EOUPlugin
from googleSheet import get_due_customers, mark_customer_contacted
from livekit.plugins import openai

load_dotenv()
plugin = EOUPlugin()
plugin.download_files()

class Assistant(Agent):
    def __init__(self, customer):
        name = customer['name']
        due_date = customer.get('due_date', 'غير معروف')  
        amount_due = customer.get('amount_due', 'غير معروف')

        print(f"Initializing Agent for {name}")
        print(f"Due Date: {due_date}, Amount Due: {amount_due}")

        # Enhanced prompt with customer data
        intro = f"""أهلاً أستاذ {name}، أنا اسلام من الجمعية، باتطمن عليك!

        معلومات العميل المهمة:
        - الاسم: {name}
        - تاريخ الاستحقاق: {due_date}
        - المبلغ المستحق: {amount_due} جنيه
"""

        full_prompt = intro + "\n\n" + PROMPT
        super().__init__(instructions=full_prompt)

        self.due_date = due_date
        self.amount_due = amount_due
        self.customer_name = name

    async def on_message(self, message, participant):
        """Override to handle specific queries before passing to LLM"""
        # Extract text from message
        text = ""
        try:
            if hasattr(message, 'text'):
                text = str(message.text).lower()
            elif isinstance(message, dict):
                text = str(message.get('text', '')).lower()
            elif hasattr(message, 'content'):
                text = str(message.content).lower()
        except Exception as e:
            print(f"Error extracting text: {e}")
            text = ""

        print(f"Processing message text: '{text}'")

        # Check for due date queries
        due_date_keywords = ["تاريخ", "موعد", "استحقاق", "متى", "ايمتى", "امتى", "موعد الدفع"]
        if any(keyword in text for keyword in due_date_keywords):
            response = f"تاريخ الاستحقاق الخاص بك هو: {self.due_date}"
            print(f"Sending due date response: {response}")
            await participant.send_text(response)
            return

        # Check for amount queries
        amount_keywords = ["مبلغ", "فلوس", "مستحق", "كام", "كم", "قيمة", "القيمة", "المبلغ"]
        if any(keyword in text for keyword in amount_keywords):
            response = f"المبلغ المستحق هو: {self.amount_due} جنيه"
            print(f"Sending amount response: {response}")
            await participant.send_text(response)
            return

        print("No specific keywords found, passing to LLM")
        await super().on_message(message, participant)

    async def on_user_speech(self, user_speech, participant):
        """Alternative method that might be called for speech recognition"""
        try:
            text = user_speech.text.lower()
            print(f"User speech detected: '{text}'")
            
            # Create a mock message object for consistency
            mock_message = {'text': text}
            await self.on_message(mock_message, participant)
            
        except Exception as e:
            print(f"Error in on_user_speech: {e}")
            await super().on_user_speech(user_speech, participant)


async def run_session(customer):
    print(f"Running session for: {customer['name']}") 

    session = AgentSession(
        llm=openai.realtime.RealtimeModel.with_azure(
            azure_deployment=os.environ["AZURE_DEPLOYMENT"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            temperature= "0.7", 
            voice="ash"
    ))
    # ... tts, stt, vad, turn_detection, etc.
    

    room_name = f"jam3eya-{customer['id']}"
    print(f"🎙️ Calling: {customer['name']} (Room: {room_name})")

    await session.start(
        room=room_name,
        agent=Assistant(customer),
    )
    await session.generate_reply()

    mark_customer_contacted(
        row_index=customer['row_index'],
        feedback="تم المكالمة بنجاح"
    )


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    customers = get_due_customers()  

    if customers:
        customer = random.choice(customers)
        await run_session(customer)
    else:
        print("✅ No customers to call.")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

