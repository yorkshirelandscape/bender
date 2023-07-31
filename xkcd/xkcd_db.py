# Importing modules
import pandas as pd
import os
import gensim
from gensim.utils import simple_preprocess
import gensim.corpora as corpora
import nltk
from nltk.corpus import stopwords
import re
from datetime import datetime
import numpy as np
import string
from pprint import pprint
from tqdm import tqdm

nltk.download('stopwords')

stop_words = stopwords.words('english')
stop_words.extend( ['alt','text'] )


def process_text(text):
    return [word for word in simple_preprocess( str(text), deacc=True )
        if word not in stop_words]


# db = os.open('xkcd.json')

df = pd.read_json( 'xkcd.json' )
df['date'] = pd.to_datetime( dict( year = df.year, month = df.month, day = df.day ) )
df = df.drop( columns = ['news','safe_title','month','year','day','img','extra_parts'] )
df['text'] = df[['title','transcript','alt']].apply( ' '.join, axis = 1 )
# df.info()


# Remove punctuation and cnvert to lowercase
df['text'] = df['text'].map( lambda x: x.translate( str.maketrans( '', '', string.punctuation ) )
                            .lower().replace('\n','') )
# Print out the first rows of comics
print( df.head() )

# split to array by word and remove stop words
df['words'] = df['text'].map( lambda x: process_text( x ) )
print( df['words'].head() )


# Create Dictionary
df['words_dict'] = df['words'].map( lambda x: corpora.Dictionary( [x] ) )
# print( df['words_dict'].head(20) )
# Term Document Frequency
tqdm.pandas(desc='Calculating word frequency...')
df['corpus'] = df['words_dict'].progress_map( lambda x: [x.doc2bow( word ) for word in df['words']] )

# Build LDA model
tqdm.pandas(desc='Building models...')
df['lda'] = df.progress_apply( lambda x: gensim.models.LdaMulticore( corpus = x['corpus'],
                                                            id2word = x['words_dict'],
                                                            num_topics = 1,
                                                            workers = 3
                                                          ), axis = 1 
                    )
# summarize each model by producting the first 3-word topic of each row
tqdm.pandas(desc='Populating keywords...')
df['keywords'] = df['lda'].progress_map( lambda x: x.print_topics( num_topics = 1, num_words = 3 )[0][1] )
print( df[['text','keywords']].head() )


"""


import requests
import json
import re
import time
import random
import sys
import os
import lda
import numpy as np
from collections import defaultdict

def summarize(input):
    documents = re.findall(r'[^.!?\n]+[.!?\]}]+', input)
    return lda.lda(documents, 1, 3)

def appendJSON(file, data):
    jFile = []
    try:
        with open(file, 'r') as f:
            jFile = json.load(f)
    except:
        pass
    cNum = data['num']
    if not any(c['num'] == cNum for c in jFile):
        jFile.append(data)
        with open(file, 'w') as f:
            json.dump(jFile, f, indent=2)

async def getComic(i):
    response = await requests.get(f'https://xkcd.com/{i}/info.0.json')
    return response.json()

async def getComics(x, n=1):
    for i in range(x, x + n):
        comic = None
        try:
            comic = await getComic(i)
        except:
            print(f'No comic #{i}.')
            continue
        data = ' '.join([comic['title'], comic['transcript'], comic['alt']])
        comic['summary'] = summarize(data)
        try:
            appendJSON('xkcd.json', comic)
            print(f'Imported comic #{i}.')
        except:
            print(f'Comic #{i} already imported.')

def getMaxComic(file):
    with open(file, 'r') as f:
        jFile = json.load(f)
    return max(c['num'] for c in jFile)

def main():
    mc = getMaxComic('xkcd.json')
    asyncio.run(getComics(mc + 1))

if __name__ == '__main__':
    main()

"""