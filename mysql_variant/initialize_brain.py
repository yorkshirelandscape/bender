import os
import time
import cobe.brain as Cobe
import MySQLdb
from MySQLdb.constants import CR as MySQLdb_CR
from dotenv import load_dotenv

load_dotenv()

settings = {}
settings["MYSQL_HOST"]            = os.getenv("MYSQL_HOST")
settings["MYSQL_PORT"]            = int(os.getenv("MYSQL_PORT"))
settings["MYSQL_USERNAME"]        = os.getenv("MYSQL_USERNAME")
settings["MYSQL_ROOT_PASSWORD"]   = os.getenv("MYSQL_ROOT_PASSWORD")
settings["MYSQL_DB"]              = os.getenv("MYSQL_DB")

brain = None
while not brain:
	try:
		brain = Cobe.Brain(settings["MYSQL_HOST"], settings["MYSQL_PORT"], settings["MYSQL_USERNAME"], settings["MYSQL_ROOT_PASSWORD"], settings["MYSQL_DB"])
	except MySQLdb._exceptions.OperationalError as e:
		if e.args[0] != MySQLdb_CR.CONN_HOST_ERROR:
			raise
		brain = None
		print("Waiting for DB to go UP...")
		time.sleep(20)

print("CONNECTED TO DB!")

brain.init("cobe.brain")