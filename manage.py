from flask.ext.script import Manager
import kevslist as kl
import pymongo
from pprint import pprint

manager = Manager(kl.app)


@manager.command
def create_indicies():
    mongo, db = kl.connect_mongo()

    print(db.items.create_index([('posted_at', pymongo.DESCENDING), ('feed_ids', pymongo.ASCENDING)]))
    print(db.items.create_index('link', unique=True))

    mongo.close()


@manager.command
def parse_feeds():
    mongo, db = kl.connect_mongo()

    pprint(kl.parse_feeds(db), indent=4)

    mongo.close()


if __name__ == "__main__":
    manager.run()
