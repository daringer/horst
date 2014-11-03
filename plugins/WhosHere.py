#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from abstract import AbstractPlugin

__metaclass__ = type

class WhosHere(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command": re.compile(r"(?P<nick>.*)")}
    provide = ["whoshere"]
    
    def react(self, data):
        data.chan << ", ".join(u.name for u in data.chan.users)
                        
    doc = { "whoshere" : ("whoshere", "Ich sage wer alles in dem Channel rumhängt") }
            #"whois" : ("whois <nick>", "Ich geb dir den Hostname von 'nick'") }
    __doc__ = "Giving additional channel and user information"
