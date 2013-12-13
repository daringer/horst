#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from database import BaseRecord, IntegerField, StringField
from abstract import AbstractPlugin

__metaclass__ = type

class SpellcheckRecord(BaseRecord):
    word = StringField(unique=True)
    added = IntegerField()
    user = StringField()
    
class SpellCheckIgnore(AbstractPlugin):
    author = "andieh"
    react_to = {"public_command" : re.compile("(?P<words>.+)")}
    provide = ["ignoriere", "korrigiere"]
    
    def react(self, data):
        now = int(time.time())
        words = data.line["words"].split()
        
        # add a new word    
        if data.command == "ignoriere":
            for insert in words:
                u = SpellcheckRecord.objects(word=insert.lower())
                if u:
                    data.chan.send("%s ignoriere ich schon seit dem %s. Befehl von %s!" % (u.word, time.strftime("%d.%m.%Y",time.localtime(u.added)), u.user))
                else:
                    u = SpellcheckRecord.create_or_get(word=insert, added=now, user=data.user.name)
                    u.save()
                    data.chan.send("In Zukunft ignoriere ich %s, Rechtschreibprofi!" % insert)                    
        
        # remove a word
        if data.command == "korrigiere":
            for remove in words:
                u = SpellcheckRecord.objects(word=remove.lower())
                if u:
                    data.chan.send("Okee, okee, dann ignoriere ich halt in Zukunft wieder %s!" % remove)
                    u.destroy()
                else:
                    data.chan.send("Du Depp, %s ignorier ich doch überhaupt nicht!" % remove)
            
    def get_short_help(self):
        return "%s(ignoriere|korrigiere) <wort1> [... wortN]" % (self.command_prefix)
        
    def get_full_help(self):
        return ["ignoriert die angegebenen Wörter in Zukunft beim Spellcheck", 
                "oder entfernt die Wörter aus der Datenbank, um sie in Zukunft doch wieder als Falsch anzuzeigen"] 
        
