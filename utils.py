#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
import pickle
import time

from time import time as timestamp

from config import Config

__metaclass__ = type

class DataException(Exception):
    pass

def strip_nickname(nick):
    """Remove leading special characters from nickname"""

    # catch non-string-alike input
    if nick is None or not hasattr(nick, "__getitem__"):
        return nick

    real_nick = nick
    if real_nick[0] == "&" or real_nick[0] == "@" or real_nick[0] == "!":
        return real_nick[1:]
    return real_nick

class FancyPrint:
    def __init__(self, raw):
        self.raw = raw 

    def get(self):
        return str(self)

class FancyTime(FancyPrint):
    def __str__(self):
        dtup = time.localtime(self.raw)
        return str(self.raw//(60*60)) + time.strftime(":%M:%S", dtup)

class FancyDateTime(FancyPrint):
    def __str__(self):
        dtup = time.localtime(self.raw)
        return time.strftime("%d. %b %Y %H:%M:%S", dtup)

class FancyDate(FancyPrint):
    def __str__(self):
        dtup = time.localtime(self.raw)
        return time.strftime("%d. %b %Y", dtup)

class FancyFloat(FancyPrint):
    def __str__(self):
        if self.raw > 100:
            return str(round(self.raw))
        elif self.raw < 1:
            return str(round(self.raw, 4))
        elif self.raw < 10:
            return str(round(self.raw, 2))
        else:
            return str(round(self.raw, 1))

class Data:
    _vars = ["line", "line_raw", "reaction_type", "chan", "user", "command"]
    def __init__(self, **kw):
        for k in self._vars:
            setattr(self, k, kw[k] if k in kw else None)

    def __repr__(self):
        return "<Data {}>".format(", ".join("{}={}".format(k, getattr(self, k)) \
                    for k in self._vars))
    __str__ = __repr__
        
class Channel:
    def __init__(self, name, conn):
        self.name = name
        self.connection = conn
        self.join_time = timestamp()
        self.users = []

        # if true, never say something in public
        self.quiet = False
    
    def __eq__(self, other):
        return self.name == other.name
    
    def send(self, msg):
        """Sends a single str to the channel and handles a list of str as multiple lines"""
        msg = [msg] if not isinstance(msg, (tuple, list)) else msg
        for m in msg:
            self.connection.privmsg(self.name, m)
    
    def __lshift__(self, msg):
        """Shortcut for .send() - just do a: chan_obj << "my text to send"""
        if not self.silent:
            self.send(msg)
    
    def __repr__(self):
        return "<Channel name=%s join_time=%s users=%s>" % \
            (self.name, self.join_time, ", ".join(x.__repr__() for x in self.users))
    __str__ = __repr__

class User:
    def __init__(self, name, hostname, connection):
        self.name = name
        self.connection = connection
        self.hostname = hostname
        self.channels = []
        
    def __eq__(self, other):
        return self.name == other.name
            
    # don't use send() - most clients open a new tab/window for private msgs
    # this is not what we want, notice() works fine and is shown in the current chan
    def send(self, msg):
        """Sends a single str as private message and handles a list of str as multiple lines"""
        msg = [msg] if not isinstance(msg, list) else msg
        for m in msg:
            self.connection.privmsg(self.name, m)
        
    def notice(self, msg):
        """Sends a single str as notice to the user and handles a list of str as multiple lines"""
        msg = [msg] if not isinstance(msg, list) else msg
        for m in msg:
            self.connection.notice(self.name, m)

    def __lshift__(self, msg):
        """Shortcut for .notice() - just do a: chan_obj << "my text to send"""
        self.notice(msg)   

    def __repr__(self):
        return "<User name={} channels={} hostname={}>". \
                format(self.name, ", ".join(c.name for c in self.channels), self.hostname)
    __str__ = __repr__
