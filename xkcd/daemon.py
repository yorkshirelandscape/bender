from ingest import get_comics, get_latest_num, get_max_saved
from summarize import summarize
import schedule
import time

def job():
    mc = get_max_saved("xkcd/xkcd.json")
    lc = get_latest_num()
    get_comics(mc + 1, lc - mc)
    summarize()
    return

schedule.every().day.at("12:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60) # wait one minute