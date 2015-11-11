from flask import Flask, g, render_template, request, redirect, url_for, jsonify
import pymongo
from bson.objectid import ObjectId
import feedparser
import datetime
import time
import math

import os


app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


@app.route('/', defaults={'feed_id': None})
@app.route('/feed/<feed_id>')
def index(feed_id):
    items_per_page = 24
    page = int(request.args.get('page', 0))
    query = {}

    if feed_id:
        query['feed_ids'] = {'$in': [feed_id]}

    feeds = g.db.feeds.find()
    items = g.db.items.find(query).sort('posted_at', pymongo.DESCENDING).limit(items_per_page).skip(items_per_page * page)
    total_pages = math.ceil(g.db.items.count() / items_per_page)

    return render_template(
               'index.html.jade',
                current_feed=feed_id,
                feeds=feeds,
                items=items,
                total_pages=total_pages,
                current_page=page
            )


# updates all feeds, only called manually from the browser
@app.route('/feeds/parse')
def parse_feeds_endpoint():
    return jsonify(parse_feeds(g.db))


def parse_feeds(db):
    modified_feeds = {}
    for feed in db.feeds.find():
        feed_id = str(feed['_id'])
        feed['num_modified'] = parse_feed(db, feed_id, feed['url'])
        feed['_id'] = feed_id
        modified_feeds[feed_id] = feed

    return modified_feeds


# updates feed, only called manually from the browser
@app.route('/feed/<feed_id>/parse')
def parse_feed_endpoint(feed_id):
    feed_object_id = ObjectId(feed_id)
    feed = g.db.feeds.find_one({'_id': feed_object_id})
    return jsonify(num_modified=parse_feed(g.db, feed_id, feed['url']))


def parse_feed(db, feed_id, url):
    rss = feedparser.parse(url)

    num_modified = 0

    # for each item, add it to the collection if doesnt exist, otherwise
    # if exists, ensure feed_id in lists of feed_ids, always update last_seen
    for entry in rss.entries:
        entry_attrs = {
            'title': entry['title'],
            'link': entry['link'],
            'description': entry['description'],
            'picture': entry['enc_enclosure']['resource'],
            'posted_at': datetime.datetime.fromtimestamp(time.mktime(entry['date_parsed'])),
            'parsed_at': datetime.datetime.now()
        }

        num_modified += db.items.update_one(
            {'link': entry['link']},
            {
                '$set': {'last_seen_at': datetime.datetime.now()},
                '$setOnInsert': entry_attrs,
                '$addToSet': {'feed_ids': feed_id}
            },
            upsert=True
        ).modified_count

    return num_modified


# serves requests from form on /feeds
@app.route('/feeds', methods=['GET', 'POST'])
def feeds_rest():
    if request.method == 'POST':
        g.db.feeds.insert_one({
            'name': request.form['name'],
            'url': request.form['url']
        })

    return render_template('feeds.html.jade', feeds=g.db.feeds.find())


# responds to ajax requests to edit or delete feed from /feeds
@app.route('/feed', methods=['POST'])
def feed_rest():
    feed_object_id = ObjectId(request.form['feed_id'])
    if request.form['_method'] == 'DELETE':
        g.db.feeds.delete_one({'_id': feed_object_id})

    elif request.form['_method'] == 'PATCH':
        g.db.feeds.update_one(
            {'_id': feed_object_id},
            {
                '$set': {
                    'name': request.form['name'],
                }
            }
        )

    return redirect(url_for('feeds'))


def connect_mongo():
    uri = os.environ.get('MONGOLAB_URI')

    if uri:
        client = pymongo.MongoClient(uri)
        mongo = client
        db = client.get_default_database()
    else:
        client = pymongo.MongoClient()
        mongo = client
        db = client.kevslist

    return mongo, db


@app.before_request
def before_request():
    g.mongo, g.db = connect_mongo()


@app.teardown_request
def teardown_request(_):
    mongo = getattr(g, 'mongo', None)
    if mongo is not None:
        mongo.close()


if __name__ == '__main__':
    port = os.environ.get('PORT')

    if port:
        app.run(port=port)
    else:
        app.run(debug=True)
