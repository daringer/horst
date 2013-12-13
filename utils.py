#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
import pickle
import time

from time import time as timestamp

__metaclass__ = type

class DataException(Exception):
    pass


class FancyPrint:
    def __init__(self, raw):
        self.raw = raw
    def __str__(self):
        pass
    __repr__ = __unicode__ = __str__

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
        elif self.raw <= 1:
            return str(round(self.raw, 4))
        elif self.raw <= 10:
            return str(round(self.raw, 2))
        else:
            return str(round(self.raw, 1))
class Data:
    _vars = ["line", "line_raw", "reaction_type", "chan", "user", "command"]
    def __init__(self, **kw):
        for k in self._vars:
            setattr(self, k, kw[k] if k in kw else None)

    def __repr__(self):
        return "<Data %s>" % ", ".join("%s=%s" % (k, getattr(self,k)) for k in self._vars)
    __unicode__ = __str__ = __repr__
                
        
class Channel:
    def __init__(self, name, conn):
        self.name = name
        self.connection = conn
        self.join_time = timestamp()
        self.users = []
    
    def __eq__(self, other):
        return self.name == other.name
    
    def send(self, msg):
        """Sends a single str to the channel and handles a list of str as multiple lines"""
        msg = [msg] if not isinstance(msg, list) else msg
        for m in msg:
            try:
                self.connection.privmsg(self.name, m)
            except UnicodeEncodeError as e:
                self.connection.privmsg(self.name, m.encode("utf-8", "ignore"))
    
    def __lshift__(self, msg):
        """Shortcut for .send() - just do a: chan_obj << "my text to send"""
        self.send(msg)   
    
    def __repr__(self):
        return "<Channel name=%s join_time=%s users=%s>" % \
            (self.name, self.join_time, ", ".join(x.__repr__() for x in self.users))
    __unicode__ = __str__ = __repr__
 
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
        return "<User name=%s channels=%s hostname=%s>" % (self.name, ", ".join(c.name for c in self.channels), self.hostname)
    __unicode__ = __str__ = __repr__
