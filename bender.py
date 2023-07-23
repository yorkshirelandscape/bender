import os
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from cobe import brain
# from cobe.brain import Brain
# import MySQLdb
# from MySQLdb.constants import CR as MySQLdb_CR
from dotenv import load_dotenv

load_dotenv()

settings = {}
# settings["MYSQL_HOST"]            = os.getenv("MYSQL_HOST")
# settings["MYSQL_PORT"]            = int(os.getenv("MYSQL_PORT"))
# settings["MYSQL_USERNAME"]        = os.getenv("MYSQL_USERNAME")
# settings["MYSQL_ROOT_PASSWORD"]   = os.getenv("MYSQL_ROOT_PASSWORD")
# settings["MYSQL_DB"]              = os.getenv("MYSQL_DB")
settings["BOT_TOKEN"]             = os.getenv("SLACK_BOT_TOKEN")
settings["BOT_ID"]                = os.getenv("SLACK_BOT_TOKEN").split(':')[0]
settings["APP_TOKEN"]			  = os.getenv("SLACK_APP_TOKEN")
settings["CREATOR_ID"]            = os.getenv("CREATOR_ID")
settings["CREATOR_NICKNAME"]      = os.getenv("CREATOR_NICKNAME")
settings["TRIGGER_ENABLED"]       = bool(os.getenv("TRIGGER_ENABLED"))
settings["TRIGGER_WORDS"]         = os.getenv("TRIGGER_WORDS").split(",")
settings["CHAT_ALLOWLIST"]        = os.getenv("CHAT_ALLOWLIST").split(",")
settings["RANDOM_ENABLED"]        = bool(os.getenv("RANDOM_ENABLED"))
settings["RANDOM_PERCENTAGE"]     = os.getenv("RANDOM_PERCENTAGE")
settings["PRIVATE_REPLY_ENABLED"] = bool(os.getenv("PRIVATE_REPLY_ENABLED"))
settings["BLOCKLIST_WORDS"]       = os.getenv("BLOCKLIST_WORDS").split(",")
settings["LEARN_ENABLED"]         = bool(os.getenv("LEARN_ENABLED"))

# Initializes your app with your bot token and socket mode handler
app = App(token=settings["BOT_TOKEN"])

# brain = None
# while not brain:
# 	try:
# 		brain = Brain(settings["mysql_host"], settings["mysql_port"], settings["mysql_username"], settings["mysql_root_password"], settings["mysql_db"])
# 	except MySQLdb._exceptions.OperationalError as e:
# 		if e.args[0] != MySQLdb_CR.CONN_HOST_ERROR:
# 			raise
# 		brain = None
# 		print("Waiting for DB to go UP...")
# 		time.sleep(20)

# print("CONNECTED TO DB!")

# try:
# 	bender = brain.Brain('bender.brain')
# except brain.CobeError as err:
# 	print("brain dead", err)

bender = brain.Brain('bender.brain')

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

# Listens to incoming messages that contain "hello"
# To learn available listener arguments,
# visit https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html
@app.message('.*')
def message_learn(message, say):
	msg = message['text']
	bender.learn(msg)
	if 'bender' in msg:
		reply = bender.reply(msg)
    	# say() sends a message to the channel where the event was triggered
		reply = reply[1:-1]
		say(reply)


# @app.message("bender")
# def message_reply(message, say):
#     reply = bender.reply(message['text'])
#     # say() sends a message to the channel where the event was triggered
#     say(reply)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, settings["APP_TOKEN"]).start()
