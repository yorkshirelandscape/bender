import os
from dotenv import load_dotenv
from slack_sdk.rtm_v2 import RTMClient

load_dotenv()

rtm = RTMClient(token=os.environ["BOT_TOKEN"])

@rtm.on("message")
def handle(client: RTMClient, event: dict):
    if 'bender' in event['text']:
        channel_id = event['channel']
        # user = event['user'] # This is not username but user ID (the format is either U*** or W***)
        
        response = "Testing"
        
        client.web_client.chat_postMessage(
        channel=channel_id,
        text=response
        )

rtm.start()