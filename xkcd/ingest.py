import requests
import json
import argparse

# Parse arguments
parser = argparse.ArgumentParser(
    prog="xkcd Ingestor", description="Download xkcd metadata", epilog=""
)
parser.add_argument(
    "--comic",
    help="The comic number to start with (default: 0 for latest)",
    type=int,
    default=0,
)
parser.add_argument(
    "--number",
    help="The number of comics to download (default: 1)",
    type=int,
    default=1,
)
args = parser.parse_args()


def append_json(file, data):
    try:
        with open(file, "r") as f:
            jfile_temp = json.load(f)
    except:
        jfile_temp = []

    cNum = data["num"]
    if not any(c["num"] == cNum for c in jfile_temp):
        jfile_temp.append(data)
        with open(file, "w") as f:
            json.dump(jfile_temp, f, indent=2)
    else:
        raise Exception(f"Comic #{cNum} already imported.")


def get_latest_num():
    response = requests.get("https://xkcd.com/info.0.json")
    j = response.json()
    return j["num"]


def get_comic(i):
    response = requests.get(f"https://xkcd.com/{i}/info.0.json")
    return response.json()


def get_comics(x, n=1):
    for i in range(x, x + n):
        try:
            comic = get_comic(i)
        except:
            print(f"No comic #{i}.")
            continue

        # import summarize module and process comic

        try:
            append_json("xkcd/xkcd.json", comic)
            print(f"Imported comic #{i}.")
        except:
            print(f"Comic #{i} already imported.")


def get_max_saved(file):
    with open(file, "r") as f:
        jFile = json.load(f)
    return max(c["num"] for c in jFile)


def medic(file):
    with open(file, "r") as f:
        j = json.load(f)
        mc = max(c["num"] for c in j)
        missing = []
        for i in range(1, mc + 1):
            if not any(c["num"] == i for c in j):
                missing.append(i)
        for i in missing:
            get_comics(i)
    with open(file, "r") as f:
        j = json.load(f)
        j.sort(key=lambda x: x["num"])
    with open(file, "w") as f:
        json.dump(j, f, indent=2)


if args.comic == 0:
    get_comics(get_latest_num())
elif args.comic == -1:
    mc = get_max_saved("xkcd/xkcd.json")
    lc = get_latest_num()
    get_comics(mc + 1, lc - mc)
elif args.comic == -2:
    medic("xkcd.json")
else:
    get_comics(args.comic)
