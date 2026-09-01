# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import tzlocal
import uuid

from mongoengine import Document,  StringField, ListField, MapField, BooleanField, DynamicField, EmbeddedDocument, EmbeddedDocumentField, DateTimeField

class APIToken(EmbeddedDocument):
    """ Embedded document for API tokens. Contains id (used for identifying a token without using directly the hash),
    the token hash, expiration date,description and hash algorithm used. """
    token_id = StringField(required=True, default=lambda: uuid.uuid4().hex) # also used as the key in the MapField of tokens
    token = StringField(required=True)
    expires = DateTimeField(required=True)
    description = StringField(required=True)

class User(Document):
    username = StringField(required=True)
    realname = StringField(required=True)
    email = StringField(required=True)
    password = StringField()
    language = StringField(required=True, default="en")
    code_indentation = StringField(choices=["2", "3", "4", "tabs"], default="4")
    bindings = MapField(ListField()) # TODO: use custom validation or refactor
    ltibindings = MapField(StringField())
    tos_accepted = BooleanField(default=False)
    apikey = StringField(default=None)
    apitokens = MapField(EmbeddedDocumentField(APIToken), default={})
    timezone = StringField(default=lambda: tzlocal.get_localzone_name())
    pinned_courses = ListField(StringField(), default=[])
    activate = StringField()
    reset = StringField()

    meta = {"collection": "users", "indexes": ["username", "email"]}
