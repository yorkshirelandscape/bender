from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import os
import json
import markovify
import re
from slack_sdk.web import WebClient
import logging
logging.basicConfig(filename='output.log', level=logging.DEBUG)
import threading
from megahal import *

app = Flask(__name__)

load_dotenv()

DEBUG = True
STATE_SIZE = 2

megahal = MegaHAL()

PATH_TO_BRAIN = "/home/volfied/dev_bender/megahal_brain_small"

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/", app)

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["BENDER_TOKEN"]
slack_client = WebClient(slack_bot_token)


def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator


megahal.train(PATH_TO_BRAIN)

# megahal.close()  # flush changes and close

# import pdb; pdb.set_trace()
# test = model_small.make_sentence(init_state=('president',))
# print(test)

eIds = []

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    global new_messages
    global eIds

    eId = event_data["event_id"]
    logging.info(eId)
    if eId in eIds:
        logging.info(f"already seen message {eId}")
        return
    else:
        eIds.add(eId)

    message = event_data["event"]

    if message.get("subtype") is None and message.get("bot_id") is None:
        channel = message["channel"]
        text = re.sub('[^A-Za-z0-9 ]+', '', message.get('text').lower())
        megahal.learn(text)        
        
        if "bender" in text:
            logging.info(text)
            
            message = megahal.get_reply(text)
            
            slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    logging.error(str(err))


@setInterval(60*60)
def update_brain():
    megahal.sync()

stop = update_brain()


# @app.route('/', methods=['POST'])
# def challenge_response():
#     request_data = request.get_json()
#     challenge = {'challenge': request_data['challenge']}
#     return challenge, 200

# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=443, debug=True)