#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from db.fields import IntegerField, StringField, DateTimeField
from db.baserecord import BaseRecord
from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat, strip_nickname

__metaclass__ = type

class StatRecord(BaseRecord):
    nick = StringField(unique=True)
    words = IntegerField()
    chars = IntegerField()
    lines = IntegerField()
    last_activity = DateTimeField(auto_now_add=True)
    first_seen = DateTimeField(auto_now_add=True)
    seconds_online = IntegerField()
    last_online = DateTimeField(auto_now=True)

    def seen_activity(self):
        self.last_activity = int(time.time())

    def seen_online(self, rightnow=False):
        now = int(time.time())
        # rightnow is set to just reset "last_online" to now (for joins)
        self.seconds_online += (now - self.last_online) if not rightnow else 0

class Stats(AbstractPlugin):
    author = "meissna"
    react_to = {"public": re.compile(r"(?P<all>.+)"),
                "join": re.compile(r"(?P<all>.+)"),
                "leave": re.compile(r"(?P<all>.+)"),
                "enter_channel": re.compile(r"(?P<all>.+)"),
                "leave_channel": re.compile(r"(?P<all>.+)"),
                "public_command": re.compile(r"(?P<nick>.*)"),
                "nick_change":re.compile(r"(?P<old_nick>.+)")} 
    provide = ["stats"]
    
    def react(self, data):
        now = int(time.time())

        # if we enter or leave the channel inspect all users and mark as seen_online
        if data.reaction_type in ["enter_channel", "leave_channel"]:
            for u in data.chan.users:
                nick = strip_nickname(u.name)
                u = StatRecord.objects.create_or_get(nick=nick)
                u.seen_online(rightnow=data.reaction_type=="enter_channel")
    
                if not StatRecord.objects.exists(nick=nick):
                    u.save()
            return True

        # on nick change we save the old nick as seen online, and handle the new nick
        # like a "join"                
        if data.reaction_type == "nick_change":
            u = StatRecord.objects.create_or_get(nick=strip_nickname(data.line["old_nick"]))
            u.seen_online()
            u.save()
        
        # "join", "public", "public_command", "leave" reaction_type handlers
        u = StatRecord.objects.create_or_get(nick=strip_nickname(data.user.name))
        u.seen_online(rightnow=data.reaction_type in ["join", "nick_change"])
        
        if data.reaction_type == "public" and data.line.has_key("all"):
            u.seen_activity()
            u.words += len(data.line["all"].split(" ")) 
            u.chars += len(data.line["all"].replace(" ",""))
            u.lines += 1            
            
        elif data.reaction_type == "public_command":
            nick = strip_nickname(data.line["nick"] if data.line["nick"] else u.nick)
            u.seen_activity()
            show = StatRecord.objects.get(nick=nick)
            if show is None:
                data.chan << "The nick {0} does not exist in the stats-database".format(nick)
            elif data.command == "rawstats":
                data.chan << str(show)
            else:
                data.chan << "Statistiken von {}:".format(show.nick)
                data.chan << "Gesamt online: {} | zuletzt online: {}". \
                        format( FancyTime(show.seconds_online).get(), FancyDateTime(show.last_online).get() )
                data.chan << "Zuletzt aktiv: {} | zuerst aktiv: {}". \
                        format( FancyDateTime(show.last_activity).get(), FancyDateTime(show.first_seen).get() )

                if show.chars != 0 and show.seconds_online != 0:
                    data.chan << "Im Schnitt pro     Tag  | Stunde |  Minute"
                    
                    units = [ show.seconds_online/float(x) for x in (60*60*24, 60*60, 60) ]
                    
                    lines, words, chars = [ ([FancyFloat(count / x) for x in units ]) \
                            for count in [show.lines, show.words, show.chars] ]

                    for desc, (day, hour, minute) in [("Zeilen ", lines), ("Wörter ", words), ("Zeichen", chars)]:
                        #print desc, vals
                        #data.chan << "%s:%s %8s | %6s | %6s" % ((desc, (" "*(12-len(desc)))) + tuple(vals))
                        #data.chan << ("{} | {}".format(desc, str(vals)))
                        data.chan << "{:<17} {:>6} | {:>6} | {:>6}".format(desc, day, hour, minute)

                else:
                    data.chan << "Hat aber noch nicht ein einziges Zeichen geschrieben..."                
                
        # "join", "leave" reaction_type just save()            
        u.save()

    doc = {"stats"    : ("stats [nickname]", "Ich zeige die Statistiken für den <nickname>.")}
    __doc__ = "Stores and analyses statistical user data"
               
