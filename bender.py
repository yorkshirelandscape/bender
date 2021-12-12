from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import os
import markovify
import re
import math
from slack_sdk.web import WebClient
import logging
logging.basicConfig(filename='output.log', level=logging.INFO)
import threading
import subprocess
from fuzzywuzzy import process

app = Flask(__name__)

load_dotenv()

STATE_SIZE = 3

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


def tail(f, n, offset=0):
    proc = subprocess.Popen(['tail', '-n', n + offset, f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines[:, -offset]

def tup_processor(tup):
    ', '.join(tup)

# import pdb; pdb.set_trace()
# test = model_small.make_sentence(init_state=('president',))
# print(test)

try:
    logging.info('Attempting to load stored brain.')
    with open('model.json', 'r') as model_json:
        model = markovify.Text.from_json(model_json.read())
except:
    logging.info('Load failed. Rebuilding brain.')
    with open('corpus.brn', 'r') as corpus:
        model = markovify.Text(corpus.read(), state_size=STATE_SIZE)
        mj = model.to_json()
        with open('model.json', 'w') as file:
            file.write(mj)

model.compile(inplace = True)
logging.info('Ready.')

eIds = set()
new_messages = []

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    global model
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
        msgId = message.get("client_msg_id")
        text = message.get('text')
        new_messages.append(text)
        text = re.sub('[^A-Za-z0-9 ]+', '', text.lower())
        
        if "bender" in text:
            channel = message["channel"]
            
            pad = STATE_SIZE - 1
            longest_word = list(reversed(sorted([w for w in text.split() if w != 'bender'], key=len)))[0]
            words = list([w for w in text.split() if w != 'bender'])
            lwi = words.index(longest_word)
            lwip = lwi + 1
            type_order = ''
            if lwi - pad >= 0:
                seed = tuple(words[lwi - pad:lwip])
                type_order = 'A'
                # logging.info('A')
                # logging.info(seed)
            elif len(words) - lwi >= STATE_SIZE:    
                seed = tuple(words[lwi:lwip + pad])
                type_order = 'B'
                # logging.info('B')
                # logging.info(seed)
            elif len(words) >= STATE_SIZE and pad % 2 == 0:
                seed = tuple(words[lwi - int(pad / 2):lwip + int(pad / 2)])
                type_order = 'C'
                # logging.info('C')
                # logging.info(seed)
            elif len(words) >= STATE_SIZE and pad % 2 != 0:
                seed = tuple(words[lwi - int(math.ceil(pad / 2)):lwip + int(math.floor(pad / 2))])
                type_order = 'D'
                # logging.info('D')
                # logging.info(seed)
            else:
                seed = tuple(words[lwi - max(0,lwi - pad):lwip])
                type_order = 'F'
                # logging.info('F')
                # logging.info(seed)
            
            logging.info(seed)
            str_seed = ', '.join(seed)
            logging.info(str_seed)
            seed_keys = list(k for k in model.chain.model.keys() if all(x in k for x in seed))
            logging.info(seed_keys)
            match = process.extractOne(str_seed, seed_keys, processor=tup_processor)
            seed = match[0]
            
            logging.info(match)
            try:
                message = model.make_sentence(init_state=seed)
            except:
                message = model.make_sentence()
            
            logging.info(message)
            
            slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    logging.error(str(err))


@setInterval(60*60)
def update_brain():
    global new_messages
    global model
    
    logging.info('Updating brain.')
    with open('corpus.brn', 'a+') as corpus:
        for line in new_messages:
            corpus.write('\n')
            corpus.write(line)
        
        model = markovify.Text(corpus.read(), state_size=STATE_SIZE)
        corpus.close()

    mj = model.to_json()
    with open('model.json', 'w') as file:
        file.write(mj)
        file.close()

    model.compile(inplace = True)
    logging.info('Ready.')

    trunc = tail('output.log', 100)
    with open('output.log', 'w') as log:
        log.write(trunc)
        log.close()


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