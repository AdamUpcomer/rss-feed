#!/usr/bin/python
# -*- coding: utf-8 -*-
import feedparser
from rake import *
import operator
import re
import six
from six.moves import range
from collections import Counter
from difflib import SequenceMatcher

TITLE_IMPORTANCE = 2
GAME_SIMILARITY_RATIO = 0.90

feed_posts = []

# Add feed sources
sources = {'wc3': ['http://www.gosugamers.net/warcraft3/news/rss'],
           'general': ['http://www.gosugamers.net/dota2/news/rss']}
game_keywords = {'lol': ['league of legends', 'lol', 'riot'],
                 'dota2': ['dota', 'dota2', 'defense of the ancients',
                           'defense of the ancients 2', 'the international',
                           'ti7']}
rake = Rake("SmartStoplist.txt")


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def match_game(title, summary, keywords):
    for temp_game in game_keywords:
        for game_keyword in game_keywords[temp_game]:
            if game_keyword in title:
                return temp_game
            if game_keyword in summary:
                return temp_game
            for keyword in keywords:
                if similar(keyword, game_keyword) >= GAME_SIMILARITY_RATIO:
                    return temp_game
    return 'untagged'


def add_post(data, game):
    # Get keywords in title
    title_keywords = rake.run(data['title'])
    # Increase value of keywords in title
    title_keywords.update({n: TITLE_IMPORTANCE * title_keywords[n] for n in title_keywords.keys()})
    # Get keywords in summary
    summary_keywords = rake.run(data['summary_detail']['value'])
    # Combine keywords
    for keyword in summary_keywords:
        if keyword in title_keywords:
            title_keywords[keyword] += summary_keywords[keyword]
        else:
            title_keywords[keyword] = summary_keywords[keyword]
    # Sort keywords and keep top 5
    keywords_list = sorted(title_keywords.iteritems(), key=operator.itemgetter(1), reverse=True)
    keywords = [str(x[0]) for x in keywords_list[:5]]
    # Add game if not available
    if game == 'general':
        tagged_game = match_game(data['title'], data['summary_detail']['value'], keywords)
    else:
        tagged_game = game
    # Add post to our feed
    feed_posts.append({'title': data['title'],
                       'summary': data['summary_detail']['value'],
                       'link': data['links'][0]['href'],
                       'published': data['published_parsed'],
                       'keywords': keywords,
                       'game': tagged_game})


# Parse RSS feeds
for game in sources:
    for source in sources[game]:
        f = feedparser.parse(source)
        for post in f['entries']:
            # Add post to feed
            add_post(post, game)

# Sort feed on time
feed_posts = sorted(feed_posts, key=lambda x: x['published'], reverse=True)

# Print Feed
for post in feed_posts:
    print(post)







