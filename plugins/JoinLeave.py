#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from abstract import AbstractPlugin

__metaclass__ = type

class JoinLeave(AbstractPlugin):
    author = "meissna"
    react_to = {"private" : re.compile(r"(?P<channel>\#[a-zA-Z0-9]+)?"),
                "public_command" : re.compile(r"(?P<channel>\#[a-zA-Z0-9]+)?")}
    provide = ["join", "leave"]
    
    def react(self, data):
        if "channel" in data.line:
            if data.command == "join":
                self.horst_obj.connection.join(data.line["channel"])
            else:
                if data.line["channel"] in self.horst_obj.chans:
                    self.horst_obj.connection.part(data.line["channel"])
                else:
                    data.user << "ich bin gar nicht in dem channel du b00n"
        else:
            data.user << "du musst schon einen gültigen channel angeben"
    
    
    doc = { "join"  : ("join #<channel>", "Ich werde dem 'channel' beitreten"),
            "leave" : ("leave #<channel>", "Ich werde den 'channel' verlassen") }
    __doc__ = "Join and leave channels during runtime"
                
