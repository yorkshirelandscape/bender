from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import os
import json
import markovify
import re
from slack_sdk.web import WebClient

app = Flask(__name__)

load_dotenv()

MESSAGE_QUERY = "from:bender"
MESSAGE_PAGE_SIZE = 100
DEBUG = True
STATE_SIZE = 2

PATH_TO_BRAIN = "/home/volfied/bender/message_db.json"

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/", app)

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["BENDER_TOKEN"]
slack_client = WebClient(slack_bot_token)


def _load_db():
    """
    Reads 'database' from a JSON file on disk.
    Returns a dictionary keyed by unique message permalinks.
    """

    try:
        with open(PATH_TO_BRAIN, 'r') as json_file:
            messages = json.loads(json_file.read())
    except IOError:
        with open(PATH_TO_BRAIN, 'w') as json_file:
            json_file.write('{}')
        messages = {}

    return messages

def _store_db(obj):
    """
    Takes a dictionary keyed by unique message permalinks and writes it to the JSON 'database' on
    disk.
    """

    with open(PATH_TO_BRAIN, 'w') as json_file:
        json_file.write(json.dumps(obj))

    return True

def _query_messages(client, page=1):
    """
    Convenience method for querying messages from Slack API.
    """
    if DEBUG:
        print("requesting page {}".format(page))

    return client.api_call('search.messages', query=MESSAGE_QUERY, count=MESSAGE_PAGE_SIZE, page=page)

def _add_messages(message_db, new_messages):
    """
    Search through an API response and add all messages to the 'database' dictionary.
    Returns updated dictionary.
    """
    for match in new_messages['messages']['matches']:
        message_db[match['permalink']] = match['text']

    return message_db


# get all messages, build a giant text corpus
def build_text_model(state_size=2):
    """
    Read the latest 'database' off disk and build a new markov chain generator model.
    Returns TextModel.
    """
    if DEBUG:
        print("Building new model...")

    messages = _load_db()
    return markovify.Text(" ".join(messages.values()), state_size)


def format_message(original):
    """
    Do any formatting necessary to markov chains before relaying to Slack.
    """
    if original is None:
        return

    # Clear <> from urls
    cleaned_message = re.sub(r'<(htt.*)>', '\1', original)

    return cleaned_message


def update_corpus(sc, channel):
    """
    Queries for new messages and adds them to the 'database' object if new ones are found.
    Reports back to the channel where the update was requested on status.
    """

    # Load the current database
    messages_db = _load_db()
    starting_count = len(messages_db.keys())

    # Get first page of messages
    new_messages = _query_messages(sc)
    total_pages = new_messages['messages']['paging']['pages']

    # store new messages
    messages_db = _add_messages(messages_db, new_messages)

    # If any subsequent pages are present, get those too
    if total_pages > 1:
        for page in range(2, total_pages + 1):
            new_messages = _query_messages(sc, page=page)
            messages_db = _add_messages(messages_db, new_messages)

    # See if any new keys were added
    final_count = len(messages_db.keys())
    new_message_count = final_count - starting_count

    # If the count went up, save the new 'database' to disk, report the stats.
    if final_count > starting_count:
        # Write to disk since there is new data.
        _store_db(messages_db)
        sc.rtm_send_message(channel, "I have been imbued with the power of {} new messages!".format(
        new_message_count
        ))

    else:
        sc.rtm_send_message(channel, "No new messages found :(")

    if DEBUG:
        print("Start: {}".format(starting_count), "Final: {}".format(final_count),
        "New: {}".format(new_message_count))

    # Make sure we close any sockets to the other group.
    # del group_sc

    return new_message_count
    

model = build_text_model()
model_small = build_text_model(state_size=1) 
print("Ready")

# import pdb; pdb.set_trace()
# test = model_small.make_sentence(init_state=('president',))
# print(test)

new_messages = {}

# Example responder to bot mentions
@slack_events_adapter.on("app_mention")
def handle_mentions(event_data):
    event = event_data["event"]
    slack_client.chat_postMessage(
        channel=event["channel"],
        text=f"You said:\n>{event['text']}",
    )


# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    global model
    global model_small
    global new_messages

    message = event_data["event"]
    
    if message.get("subtype") is None:
        channel = message["channel"]
        msgId = message.get('ts')
        text = re.sub('[^A-Za-z0-9 ]+', '', message.get('text').lower())
        newMsg = {msgId: text}
        new_messages.update(newMsg)
        
        if text == "bender update":
            if len(new_messages) > 0:
                messages_db = _load_db()
                messages_db.update(new_messages)
                _store_db(messages_db)

                new_messages = {}

                model = build_text_model()
                model_small = build_text_model(state_size=1)

                message = "Brain updated."
            else: message = "No updates to add." 

            slack_client.chat_postMessage(channel=channel, text=message)
        
        elif "bender" in text:
            channel = message["channel"]
            
            seed = tuple(list(reversed(sorted([w for w in text.split() if w != 'bender'], key=len)))[0:STATE_SIZE])
            
            try:
                # print(seed)
                markov_chain = model.make_sentence(init_state=seed)
            except:
                seed = (seed[0],)
                # print(seed)
                try:
                    markov_chain = model_small.make_sentence(init_state=seed)
                except:
                    # print('None')
                    markov_chain = model.make_sentence()
            message = format_message(markov_chain)
            
            slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))



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