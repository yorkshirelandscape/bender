import fs
import lda
import underscore as _
import sentence_similarity as similarity
import similarity_score as simScore

def summarize(input):
    documents = re.findall(r'[^.!?\n]+[.!?\]}]+', input)
    return lda.lda(documents, 1, 3)

async def getStoredComic(file, n):
    jFile = fs.readFileSync(file)
    jFile = JSON.parse(jFile)
    comic = next((c for c in jFile if c['num'] == n), None)
    return comic

def getSummaries(file, n=None, x=1):
    jFile = fs.readFileSync(file)
    jFile = JSON.parse(jFile)
    summaries = []
    if n is not None:
        jFile = [c for c in jFile if c['num'] >= x and c['num'] <= x + n]
        summaries = jFile
    summaries = [[t['term'] for s in c['summary'] for t in s] for c in jFile]
    return summaries

async def bestComic(client, channel, num):
    limit = min(10, num)
    messages = await channel.messages.fetch(limit=limit)
    msgString = ' '.join([msg.content for msg in messages])
    input = summarize(msgString)
    corpus = getSummaries('./commands/xkcd.json')
    winkOpts = {'f': simScore.winklerMetaphone, 'options': {'threshold': 0}}
    scores = [similarity.similarity(input, c[0], winkOpts) for c in corpus]
    maxComic = max(scores, key=lambda c: c['score'])
    maxIndex = scores.index(maxComic) + 1
    return maxIndex

async def showComic(client, num):
    comic = await getStoredComic('./c
