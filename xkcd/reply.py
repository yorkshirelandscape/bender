from gensim.utils import simple_preprocess
import nltk
from nltk.corpus import stopwords
import argparse
import json
from gensim import corpora
from gensim import models
from gensim import similarities

# Parse arguments
parser = argparse.ArgumentParser(
    prog="xkcd reply", description="Find a comic that relates to a text", epilog=""
)
parser.add_argument(
    "--input",
    help="The text to match against",
)
args = parser.parse_args()

nltk.download("stopwords")

stop_words = stopwords.words("english")
stop_words.extend(["alt", "text"])


def process_text(text):
    return [
        word
        for word in simple_preprocess(str(text), deacc=True)
        if word not in stop_words
    ]


def reply(query):
    # Load the comic data
    with open("xkcd/xkcd.json", "r") as f:
        j = json.load(f)

    # Compare query to comic keywords
    # Create dictionary
    dictionary = corpora.Dictionary(c["keywords"] for c in j)

    # Create corpus
    corpus = [dictionary.doc2bow(c["keywords"]) for c in j]

    # Create tf-idf model
    tfidf = models.TfidfModel(corpus)

    # Create similarity index
    index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=len(dictionary))

    # Create query vector
    qry = process_text(query)
    query_bow = dictionary.doc2bow(qry)

    # Create tf-idf vector
    query_tfidf = tfidf[query_bow]

    # Get similarity scores
    sims = index[query_tfidf]

    # Sort similarity scores
    sims = sorted(enumerate(sims), key=lambda item: -item[1])

    # Print top result
    print(f"#{j[sims[0][0]]['num']}: {j[sims[0][0]]['title']}")
    print(f"Similarity: {sims[0][1]}")
    print(f"URL: https://xkcd.com/{j[sims[0][0]]['num']}")

    return f"https://xkcd.com/{j[sims[0][0]]['num']}"
