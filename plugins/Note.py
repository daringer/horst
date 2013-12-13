#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from db.fields import StringField, DateTimeField, BooleanField, ManyToOneRelation
from db.baserecord import BaseRecord
from abstract import AbstractPlugin
from utils import FancyDateTime

from plugins.UserAdmin import UserRecord

__metaclass__ = type

class NoteRecord(BaseRecord):
    user = ManyToOneRelation(UserRecord)
    text = StringField(length=5000000)
    created = DateTimeField(auto_now=True)
    deleted = BooleanField()

class Note(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command": re.compile("((?P<add>add)\s+(?P<text>.+))|" +
                                             "((?P<del>del)\s+(?P<del_id>[0-9]+))|" +
                                             "((?P<show>show)\s*(?P<show_id>[0-9]+)?)|" +
                                             "((?P<change>change)\s*(?P<change_id>[0-9]+)\s(?P<new_text>.+))"),
                
                "private": re.compile("((?P<add>add)\s+(?P<text>.+))|" + 
                                      "((?P<del>del)\s+(?P<del_id>[0-9]+))|" +
                                      "((?P<show>show)\s*(?P<show_id>[0-9]+)?)|" + 
                                      "((?P<change>change)\s*(?P<change_id>[0-9]+)\s(?P<new_text>.+))")}
    provide = ["note"]
    
    def react(self, data):
        whereto = data.user if data.reaction_type == "private" else data.chan
        ur = UserRecord.logged_in(data.user)
        if not ur:
            whereto << "Du musst schon angemeldet sein"        
            return False
        
        if data.line["add"]:
            note = NoteRecord(user=ur, text=data.line["text"].strip())
            note.save()
            whereto << "Habsch gespeichert..."
            
        elif data.line["del"]:
            note = NoteRecord.objects.get(rowid=int(data.line["del_id"]), deleted=False)
            if note is None:
                whereto << "Diese Note gibts doch gar nicht"
                return False
            note.deleted = True
            note.save()
            whereto << "Und is gelöscht..."
            
        elif data.line["show"]:
            if data.line["show_id"]:
                notes = NoteRecord.objects.filter(user=ur, deleted=False, rowid=int(data.line["show_id"]))
            else:
                notes = NoteRecord.objects.filter(user=ur, deleted=False)
                
            if not notes:
                whereto << "Keine Notiz(en) gefunden"
                
            for note in notes:
                # what the fuck is this, this works in Stats.py without str()!!!
                whereto << "[%5s] %25s - %s " % (note.rowid, str(FancyDateTime(note.created)), note.text)
        
        elif data.line["change"] and data.line["change_id"]:
            note = NoteRecord.objects.get(rowid=int(data.line["change_id"]))
            note.text = data.line["new_text"].strip()
            note.save()
            whereto << "Jo, is geändert..."
            
        else:
            assert False
            
        return True
    
    doc = { "note": ("note add <text>|del <id>|show [id]|change <id> <text>", "Ich bin dein Notizblock, " +
                     "hinzufügen mit 'add' löschen mit 'del' und die 'id' gibts von 'show'." + 
                     "Ändern der Notes geht auch mit 'change' und 'id'")}
