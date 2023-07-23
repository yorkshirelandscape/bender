import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from cobe.brain import Brain

# SETTINGS
settings = {}
settings["BOT_TOKEN"]             = os.getenv("SLACK_BOT_TOKEN")
settings["BOT_ID"]                = int(os.getenv("BOT_TOKEN").split(':')[0])
settings["CREATOR_ID"]            = int(os.getenv("CREATOR_ID"))
settings["CREATOR_NICKNAME"]      = os.getenv("CREATOR_NICKNAME")
settings["TRIGGER_ENABLED"]       = bool(int(os.getenv("TRIGGER_ENABLED")))
settings["TRIGGER_WORDS"]         = os.getenv("TRIGGER_WORDS").split(",")
settings["CHAT_ALLOWLIST"]        = os.getenv("CHAT_ALLOWLIST").split(",")
settings["RANDOM_ENABLED"]        = bool(int(os.getenv("RANDOM_ENABLED")))
settings["RANDOM_PERCENTAGE"]     = int(os.getenv("RANDOM_PERCENTAGE"))
settings["PRIVATE_REPLY_ENABLED"] = bool(int(os.getenv("PRIVATE_REPLY_ENABLED")))
settings["BLOCKLIST_WORDS"]       = os.getenv("BLOCKLIST_WORDS").split(",")
settings["LEARN_ENABLED"]         = bool(int(os.getenv("LEARN_ENABLED")))

# Initializes your app with your bot token and socket mode handler
app = App(token=settings["BOT_TOKEN"])

# UTILITY FUNCTIONS
# Remove the first "trigger word" detected if string is beginning with it
def remove_trigger_words(string):
	trigger_word = start_with_trigger_words(string)
	if trigger_word:
		return string[len(trigger_word):]
	return string

# Return the "trigger word" the string is beginning with. None if not detected.
def start_with_trigger_words(string):
	for word in settings["trigger_words"]:
		if string[:len(word)].lower() == word.lower():
			return string[:len(word)]
	return None

# Listens to incoming messages that contain "hello"
# To learn available listener arguments,
# visit https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html
@app.message("bender")
def message_reply(message, say):
    reply = Brain.reply(message.text)
    # say() sends a message to the channel where the event was triggered
    say(reply)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
