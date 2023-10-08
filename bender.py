import os
from random import randint
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from cobe.brain import Brain
from dotenv import load_dotenv
from xkcd.reply import reply as xkcd

load_dotenv()

settings = {}
settings["BOT_TOKEN"]             = os.getenv("SLACK_BOT_TOKEN")
settings["BOT_ID"]                = os.getenv("SLACK_BOT_TOKEN").split(':')[0]
settings["APP_TOKEN"]			  = os.getenv("SLACK_APP_TOKEN")
settings["CREATOR_ID"]            = os.getenv("CREATOR_ID")
settings["CREATOR_NICKNAME"]      = os.getenv("CREATOR_NICKNAME")
settings["TRIGGER_ENABLED"]       = bool(os.getenv("TRIGGER_ENABLED"))
settings["TRIGGER_WORDS"]         = [x.lower() for x in os.getenv("TRIGGER_WORDS").split(",")]
settings["CHAT_ALLOWLIST"]        = os.getenv("CHAT_ALLOWLIST").split(",")
settings["RANDOM_ENABLED"]        = bool(os.getenv("RANDOM_ENABLED"))
settings["RANDOM_RATIO"]          = os.getenv("RANDOM_RATIO")
settings["PRIVATE_REPLY_ENABLED"] = bool(os.getenv("PRIVATE_REPLY_ENABLED"))
settings["BLOCKLIST_WORDS"]       = os.getenv("BLOCKLIST_WORDS").split(",")
settings["LEARN_ENABLED"]         = bool(os.getenv("LEARN_ENABLED"))

# Initializes your app with your bot token and socket mode handler
app = App(token=settings["BOT_TOKEN"])

bender = Brain('bender.brain')

# UTILITY FUNCTIONS
# Remove the first "trigger word" detected if string is beginning with it
def remove_trigger_words(string):
	trigger_word = start_with_trigger_words(string)
	if trigger_word:
		return string[len(trigger_word):]
	return string

# Return the "trigger word" the string is beginning with. None if not detected.
def start_with_trigger_words(string):
	for word in settings["TRIGGER_WORDS"]:
		if string[:len(word)].lower() == word.lower():
			return string[:len(word)]
	return None

@app.event('app_mention')
def on_event(event, say):
	msg = event['text']
	if settings["LEARN_ENABLED"]:
		bender.learn(remove_trigger_words(msg))
	reply = bender.reply(msg)
	# say() sends a message to the channel where the event was triggered
	say(reply)


@app.message('xkcd')
def on_event(message, say):
	msg = message['text'].replace('xkcd', '')
	reply = xkcd(msg)
	say(reply)


# To learn available listener arguments,
# visit https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html
@app.message('.*')
def on_event(message, say):
	msg = message['text']
	if settings["LEARN_ENABLED"]:
		bender.learn(remove_trigger_words(msg))
	if any(w in msg.lower() for w in settings["TRIGGER_WORDS"]) or (settings["RANDOM_ENABLED"] and randint(0, int(settings["RANDOM_RATIO"]))==0):
		reply = bender.reply(msg)
    	# say() sends a message to the channel where the event was triggered
		say(reply)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, settings["APP_TOKEN"]).start()
