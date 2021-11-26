import json
import markovify
import re
import time
import os
from dotenv import load_dotenv
from slack_sdk.rtm_v2 import RTMClient

load_dotenv()

BOT_TOKEN = os.environ.get("FLEXO_TOKEN") 
# GROUP_TOKEN = "slack user API token"

MESSAGE_QUERY = "from:bender"
MESSAGE_PAGE_SIZE = 100
DEBUG = True
STATE_SIZE = 2

PATH_TO_BRAIN = "/home/volfied/bender/message_db.json"


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

    sc.web_client.chat_postMessage(
        channel=channel,
        text="Updating brain..."
        )

    # Messages will get queried by a different auth token
    # So we'll temporarily instantiate a new client with that token
    # group_sc = WebClient(GROUP_TOKEN)

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

rtm = RTMClient(token=os.environ["BOT_TOKEN"])

@rtm.on("message")
def handle(client: RTMClient, event: dict):
    global model
    global model_small
    global STATE_SIZE
    if 'bender update' in event['text']:
        channel_id = event['channel']
        
        uc = update_corpus(client, channel_id)

        if uc > 0:
            model = build_text_model()
            model_small = build_text_model(state_size=1)
        
            client.web_client.chat_postMessage(
            channel=channel_id,
            text="Corpus updated."
            )
        
    elif 'bender' in event['text']:
        channel_id = event['channel']
        text = event['text']
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
        response = format_message(markov_chain)
        
        client.web_client.chat_postMessage(
        channel=channel_id,
        text=response
        )

rtm.start()
        

# def main():
#     """
#     Startup logic and the main application loop to monitor Slack events.
#     """

#     # build the text model
#     model = build_text_model()

#     # Create the slackclient instance
#     sc = RTMClient(token=BOT_TOKEN, connect_method='rtm.start')

#     # Connect to slack
#     if not sc.start():
#            raise Exception("Couldn't connect to slack.")
       
#     # Where the magic happens

#     while True:
#         # Examine latest events
#         for slack_event in sc.rtm_read():

#             # Disregard events that are not messages
#             if not slack_event.get('type') == "message":
#                 continue

#             message = slack_event.get("text")
#             user = slack_event.get("user")
#             channel = slack_event.get("channel")

#             if not message or not user:
#                 continue

#             ######
#             # Commands we're listening for.
#             ######

#             if "bender" in message.lower():
#                 markov_chain = model.make_sentence()
#                 sc.rtm_send_message(channel, format_message(markov_chain))

#             if "level up bender" in message.lower():
#                 # Fetch new messages.  If new ones are found, rebuild the text model
#                 if update_corpus(sc, channel) > 0:
#                     model = build_text_model()

#     # Sleep for half a second
#     time.sleep(0.5)


# if __name__ == '__main__':
#    main()