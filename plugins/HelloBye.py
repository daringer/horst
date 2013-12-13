#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time
from random import choice


from db.fields import IntegerField, StringField, DateTimeField
from db.baserecord import BaseRecord
from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat

__metaclass__ = type

class HelloBye(AbstractPlugin):
    author = "meissna"
    react_to = {"join": re.compile(r"(?P<all>.+)"),
                "leave": re.compile(r"(?P<all>.+)") } 
    
    
    _hello_texts = ["Sers %(nick)s", "Servus %(nick)s", "Hallo %(nick)s", "Hi %(nick)s", "Was geht %(nick)s", 
                    "Guude %(nick)s", "Ei %(nick)s", "Moie %(nick)s", "Moin %(nick)s", "Aloha %(nick)s",
                    "Holla %(nick)s", "Bonjour %(nick)s", "Grüß Gott %(nick)s", "Grüß di %(nick)s", 
                    "Was geeeht abbbb %(nick)s", "Na wie %(nick)s?", "Alles fit %(nick)s?", "Du wieder %(nick)s",
                    "Is klar, %(nick)s wieder", "Und nochmal %(nick)s", "Ach was, %(nick)s du hier?",
                    "Schon wieder %(nick)s oder was?", "Endlich, %(nick)s auf dich hab ich gewartet",
                    "Boah, net %(nick)s schon wieder" ]
                    
    _bye_texts =   ["Bye %(nick)s", "Adios %(nick)s", "Fuerti %(nick)s", "Hau nei %(nick)s", "Und tschüß %(nick)s",
                    "Tschö %(nick)s", "Un wech %(nick)s", "Hau ab %(nick)s", "Gott sei dank is %(nick)s weg", 
                    "So %(nick)s weg, jetzt kanns los gehen", "Los holt das Bier raus, %(nick)s is weg", "Winke %(nick)s", 
                    "Bye Bye %(nick)s", "Kommst du wieder %(nick)s?", "Eh endlich ohne %(nick)s hier", "Gott sei dank, endlich Ruh",
                    "Meine Güte jetzt gehen alle", "Lass mich nicht allein %(nick)s", "Neeeeein, %(nick)s nicht gehen",
                    "So das war jetzt auch langsam Zeit, dass %(nick)s geht"]
    
    def react(self, data):
        dct = {"nick" : data.user.name}
        if data.reaction_type == "join":
            data.chan << choice(self._hello_texts) % dct
        elif data.reaction_type == "leave":
            data.chan << choice(self._bye_texts) % dct
        else:
            assert False

    __doc__ = "Writes some random welcome phrase, also a flame after someone left"
