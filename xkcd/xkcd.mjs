/* eslint-disable max-len */
import fs from 'fs';
import lda from 'lda';
import _ from 'underscore';
import similarity from 'sentence-similarity';
import simScore from 'similarity-score';

const summarize = (input) => {
  const documents = input.match(/[^.!?\n]+[.!?\]}]+/g);
  return lda(documents, 1, 3);
};

const getStoredComic = async (file, n) => {
  let jFile = fs.readFileSync(file);
  jFile = JSON.parse(jFile);
  const comic = jFile.find((c) => c.num === n);
  return comic;
};

const getSummaries = (file, n = null, x = 1) => {
  let jFile = fs.readFileSync(file);
  jFile = JSON.parse(jFile);
  let summaries = [];
  if (n !== null) {
    jFile = jFile.filter((c) => c.num >= x && c.num <= x + n);
    summaries = jFile;
  }
  summaries = jFile.map((c) => c.summary.map((s) => s.map((t) => t.term)));
  return summaries;
};

const bestComic = async (client, channel, num) => {
  const limit = Math.min(10, num);
  const messages = await channel.messages.fetch({ limit });
  const msgString = messages.map((msg) => msg.content).join(' ');
  const input = summarize(msgString);
  const corpus = getSummaries('./commands/xkcd.json');
  const winkOpts = { f: simScore.winklerMetaphone, options: { threshold: 0 } };
  const scores = corpus.map((c) => similarity(input, c[0], winkOpts));
  const maxComic = _.max(scores, (c) => c.score);
  const maxIndex = scores.indexOf(maxComic) + 1;
  return maxIndex;
};

const showComic = async (client, num) => {
  const comic = await getStoredComic('./commands/xkcd.json', num);
  const url = comic.img;
  const opts = { title: comic.title, footer: comic.alt };
  const msg = await client.embedImage(url, opts);
  return msg;
};

const getxkcd = async (client, channel, num, get = false) => {
  let number;
  if (!get) {
    number = bestComic(client, channel, num);
  } else { number = num; }
  return showComic(client, number);
};

export default async function xkcd(client, channel, num, get = false) {
  return getxkcd(client, channel, num, get);
}
