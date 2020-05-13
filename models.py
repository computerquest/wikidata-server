from db import db


class Node(db.Document):
    wid = db.StringField(required=True, unique=True)
    children = db.MapField(db.StringField(), required=False)
    label = db.StringField(required=True)
