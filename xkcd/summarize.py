import pandas as pd
import gensim
from gensim.utils import simple_preprocess
from gensim.test.utils import common_texts
import gensim.corpora as corpora
import nltk
from nltk.corpus import stopwords
import re
import json
import string
from tqdm import tqdm

nltk.download("stopwords")

stop_words = stopwords.words("english")
stop_words.extend(["alt", "text"])

def process_text(text):
    return [
        word
        for word in simple_preprocess(str(text), deacc=True)
        if word not in stop_words
    ]

def summarize():
    df = pd.read_json("xkcd/xkcd.json")
    df = df[df['keywords'].isnull()]
    df["date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=df.day))
    df = df.drop(
        columns=["news", "safe_title", "month", "year", "day", "img"]
    )  # ,'extra_parts'] )
    df["text"] = df[["title", "transcript", "alt"]].apply(" ".join, axis=1)
    # df.info()

    # Remove punctuation and cnvert to lowercase
    df["text"] = df["text"].map(
        lambda x: x.lower()
        .replace("alt:", "")
        .replace("\n", " ")
        .translate(str.maketrans("", "", string.punctuation))
    )

    # Print out the first rows of comics
    # print( df.head() )

    # split to array by word and remove stop words
    df["words"] = df["text"].map(lambda x: process_text(x))
    # print( df['words'].head() )

    # Build common dictionary
    print("Building common dictionary...")
    dct = corpora.Dictionary(common_texts)


    # Expand dictionary to include all words in all comics
    print("Learning new words...")
    df["words"].map(lambda x: dct.add_documents([x]))
    # print( df['words_dict'].head(20) )

    # Build out a corpus for each comic
    print("Building comic corpora...")
    df["corpus"] = df["words"].map(lambda x: [dct.doc2bow(x)])


    # Build LDA model for each comic
    tqdm.pandas(desc="Building comic LDAs...")
    df["lda"] = df["corpus"].progress_apply(
        lambda x: gensim.models.LdaMulticore(corpus=x, id2word=dct, num_topics=1, workers=3)
    )

    # summarize each model by producting the first 3-word topic of each row
    tqdm.pandas(desc="Populating keywords...")
    df["keywords"] = df["lda"].progress_map(
        lambda x: re.findall(
            r"(?<=\*\")\w+\b", x.print_topics(num_words=5)[0][1], flags=re.IGNORECASE
        )
    )
    # print( df[['text','keywords']].head() )

    f = open("xkcd/xkcd.json", "r")
    j = json.load(f)

    for c in j:
        if 'keywords' not in c:
            print( c['num'])
            c["keywords"] = df[df["num"] == c["num"]]["keywords"].values[0]

    f = open("xkcd/xkcd.json", "w")
    json.dump(j, f, indent=2)
