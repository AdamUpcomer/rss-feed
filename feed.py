#!/usr/bin/python
# -*- coding: utf-8 -*-
import feedparser
import operator
import re
from rake import Rake
import Levenshtein

# Constants
TITLE_IMPORTANCE = 2  # Multiplicative factor for keywords associated with title
KEYWORD_SIMILARITY_RATIO = 0.5  # Ratio for keyworda to be considered similar
SIMILAR_KEYWORD_REQ = 2  # Number of keywords that need to be similar for article grouping
MAX_WORD_LENGTH = 3  # Max number of words in keyword phrase


feed_posts = []
# Add feed sources
sources = {'general': ['http://www.mmogames.com/tag/esports/feed/',
                       'http://www.gosugamers.net/news/rss']}
game_keywords = {'lol': ['league of legends', 'lol', 'riot'],
                 'dota2': ['dota', 'dota2', 'defense of the ancients',
                           'defense of the ancients 2', 'the international',
                           'ti7'],
                 'csgo': ['csgo', 'counter-strike', 'counter strike', 'cs-go',
                          'counter-strike:global offensive'],
                 'overwatch': ['overwatch'],
                 'wow': ['wow', 'world of warcraft'],
                 'hots': ['hots', 'heroes of the storm'],
                 'sc': ['starcraft 2', 'starcraft', 'sc2']}


rake = Rake("SmartStoplist.txt", max_words_length=MAX_WORD_LENGTH)


def similar(a, b):
    if type(a) is list:
        similar_keywords = 0
        for a_val in a:
            for b_val in b:
                if Levenshtein.ratio(a_val, b_val) > KEYWORD_SIMILARITY_RATIO:
                    similar_keywords += 1
        return similar_keywords >= SIMILAR_KEYWORD_REQ
    return Levenshtein.ratio(a, b) > KEYWORD_SIMILARITY_RATIO


def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


def match_game(title, summary, keywords):
    for temp_game in game_keywords:
        for game_keyword in game_keywords[temp_game]:
            if game_keyword in title:
                return temp_game
            if game_keyword in summary:
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
            continue
        for temp_keyword in title_keywords:
            if similar(temp_keyword, keyword):
                title_keywords[temp_keyword] += summary_keywords[keyword]
                break
        title_keywords[keyword] = summary_keywords[keyword]
    # Sort keywords and keep top 5
    keywords_list = sorted(title_keywords.iteritems(), key=operator.itemgetter(1), reverse=True)
    keywords = [str(x[0]) for x in keywords_list[:5]]
    # Add game if not available
    if game == 'general':
        tagged_game = match_game(data['title'], data['summary_detail']['value'], keywords)
    else:
        tagged_game = game
    # Check if any post matches this one
    for post in feed_posts:
        if similar(post['keywords'], keywords) > KEYWORD_SIMILARITY_RATIO:
            # Decide which post to add here
            return
    # Add post to our feed
    feed_posts.append({'title': remove_tags(data['title']),
                       'summary': remove_tags(data['summary_detail']['value']),
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
    print("----------------- POST ------------------")
    print("TITLE: " + post['title'])
    print("SUMMARY: " + post['summary'])
    print("KEYWORDS: " + str(post['keywords']))
    print("GAME: " + post['game'])
    print(" ")
    print(" ")







