from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import os
import json
import markovify
import re
import math
from slack_sdk.web import WebClient
import logging

from bender import STATE_SIZE
logging.basicConfig(filename='output.log', level=logging.INFO)
import threading
import subprocess
from fuzzywuzzy import process

app = Flask(__name__)

load_dotenv()

PATH_TO_BRAIN = "/home/volfied/fuzzy/corpus"

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
    return ' '.join(tup)

def make_reply(seed):
    global model
    str_seed = ', '.join(seed)
    seed_keys = list(k for k in model.chain.model.keys() if all(x in k for x in seed))
    match = process.extractOne(str_seed, seed_keys, processor=tup_processor)
    match_key = match[0]
    logging.info(match_key)
    reply = model.make_sentence(init_state=match_key)
    logging.info(reply)
    if reply is None:
        raise Exception('No reply.')
    else: 
        return reply

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

text = 'My home is in North America.'
            
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

message = None
for (i, k) in zip(range(STATE_SIZE, 0, -1), range(STATE_SIZE)):
    if message is None:
        try:
            if type_order == 'A':
                seed = seed[-i:]
                # logging.info(f'A: {seed}')
                message = make_reply(seed)
            elif type_order == 'B':
                seed = seed[:i]
                # logging.info(f'B: {seed}')
                message = make_reply(seed)
            elif type_order == 'C':
                seed = seed[0 + math.floor(k/2):STATE_SIZE - math.ceil(k/2)]
                # logging.info(f'C: {seed}')
                message = make_reply(seed)
            elif type_order == 'D':
                seed = seed[0 + math.ceil(k/2):STATE_SIZE - math.floor(k/2)]
                # logging.info(f'D: {seed}')
                message = make_reply(seed)
            else:
                seed = seed[:-i]
                # logging.info(f'F: {seed}')
                message = make_reply(seed)
        except:
            pass
    
        logging.info(seed)
        logging.info(message)
        logging.info(f'{i} succeeded')
        
if message is None:
    message = model.make_sentence()
logging.info(message)

# longest_word = 'America'
# seed = ('North', 'America')
# str_seed = ' '.join(seed)
# # lw_keys = list(k for k in model.chain.model.keys() if longest_word in k)
# # logging.info(lw_keys)
# # match = process.extractOne(longest_word, lw_keys)
# seed_keys = list(k for k in model.chain.model.keys() if all(x in k for x in seed))
# logging.info(seed_keys)
# match = process.extractOne(str_seed, seed_keys, processor=tup_processor)
# logging.info(match)
# seed = match[0]
# logging.info(seed)

# try:
#     message = model.make_sentence(init_state=seed)
# except:
#     message = model.make_sentence()

# logging.info(message)