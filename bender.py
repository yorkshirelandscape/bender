from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import os
import re
from slack_sdk.web import WebClient
import logging
logging.basicConfig(filename='output.log', level=logging.DEBUG)
import threading
import subprocess

from brain import Brain

app = Flask(__name__)

load_dotenv()

DEBUG = True
STATE_SIZE = 3

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/", app)

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["BENDER_TOKEN"]
slack_client = WebClient(slack_bot_token)

brain = Brain("/home/volfied/bender/message_db.json")


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


def tail(f, n, offset=0):
    proc = subprocess.Popen(['tail', '-n', n + offset, f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines[:, -offset]


def format_message(original):
    """
    Do any formatting necessary to markov chains before relaying to Slack.
    """
    if original is None:
        return

    # Clear <> from urls
    cleaned_message = re.sub(r'<(htt.*)>', '\1', original)

    return cleaned_message


new_messages = {}
brain.learn_new_messages(new_messages)
eIds = set()

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    global models
    global new_messages
    global eIds

    eId = event_data["event_id"]
    if eId in eIds:
        logging.info(f"already seen message {eId}")
        return
    else:
        eIds.add(eId)

    message = event_data["event"]

    if message.get("subtype") is None and message.get("bot_id") is None:
        channel = message["channel"]
        msgId = message.get("client_msg_id")
        text = re.sub('[^A-Za-z0-9 ]+', '', message.get('text').lower())
        newMsg = {msgId: text}
        new_messages.update(newMsg)
        
        if "bender" in text:
            channel = message["channel"]
            
            pad = STATE_SIZE - 1
            longest_word = list(reversed(sorted([w for w in text.split() if w != 'bender'], key=len)))[0]
            words = list([w for w in text.split() if w != 'bender'])
            lwi = words.index(longest_word)
            lwip = lwi + 1
            if lwi - pad >= 0:
                seed = tuple(words[lwi - pad:lwip])
                # logging.info('A')
                # logging.info(seed)
            elif len(words) - lwi >= STATE_SIZE:
                seed = tuple(words[lwi:lwip + pad])
                # logging.info('B')
                # logging.info(seed)
            elif len(words) >= STATE_SIZE and pad % 2 == 0:
                seed = tuple(words[lwi - int(pad / 2):lwip + int(pad / 2)])
                # logging.info('C')
                # logging.info(seed)
            elif len(words) >= STATE_SIZE and pad % 2 != 0:
                seed = tuple(words[lwi - int((pad - 1) / 2) - 1:lwip + int((pad - 1) / 2)])
                # logging.info('D')
                # logging.info(seed)
            else:
                seed = tuple(words[lwi - max(0,lwi - pad):lwip])
                # logging.info('F')
                # logging.info(seed)
            
            markov_chain = None
            for i in range(pad, -1, -1):
                # logging.info(i)
                model = brain.models[i]
                if markov_chain is None:
                    try:
                        seed = seed[0:i+1]
                        # logging.info(seed)
                        markov_chain = model.make_sentence(init_state=seed)
                        # logging.info(f'{i} succeeded')
                    except:
                        pass
            if markov_chain is None:
                markov_chain = brain.models[pad].make_sentence()
            message = format_message(markov_chain)
            
            slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    logging.error(str(err))


@setInterval(60*60)
def update_brain():
    global new_messages
    global model
    brain.learn_new_messages(new_messages)

    trunc = tail('output.log', 100)
    with open('output.log', 'w'):
        trunc


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
