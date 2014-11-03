#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from db.fields import BaseRecord, IntegerField, StringField, FloatField, DateTimeField, BooleanField
from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat, FancyDate

__metaclass__ = type

# a Record to hold the plugin data
# handle Records like that:
#    m = MyRecord(mystring="something", mydecimal=12, myfloat=123.42)
#    m = MyRecord.objects.get_or_create(mystring="unique_identifier")
#    m.mydecimal = 1234
#    m.myfloat = 1234.3123
#    m.save()
#
#    # delete an object
#    m.destroy()
#
#    m = MyRecord.objects.get(mystring="bla")
#    m = MyRecord.objects.get(mystring="bla")
#    assert isinstance(m, MyRecord) or m is None
#    
#    m = MyRecord.objects.filter(mydecimal=12)
#    m = MyRecord.objects.all() 
#    m = MyRecord.objects.exclude(myfloat=123.42)
#    assert (isinstance(x, MyRecord) for x in m) and isinstance(m, list)
#

class SomeRecordAlsoCouldBeImported(BaseRecord):
    pass

class MyRecord(BaseRecord):
    mystring = StringField(length=100, unique=True)
    mydecimal = IntegerField()
    myfloat = FloatField()
    pub_date = DateTimeField(auto_now_add=True) ## is set to now() on objectcreation
    upd_date = DateTimeField(auto_now=True) ## is set to now() on every save() call
    mybool = BooleanField() ## 1 or 0 but also True and False
    myoptions = OptionField(["this","field","may","only","have","one","of","these","values"], default="field")

    # an relation ONE MyRecord object points to MANY SomeRecordAlsoCouldBeImported objects
    # one_to_n is replaced with a DataManager object, 
    # which behaves like BaseRecord::objects (i.e.: filter, get...)
    one_to_n = OneToManyRelation(SomeRecordAlsoCouldBeImported)

    def some_record_manipulating_method(self):
        pass

# The plugin class has to be the same name (including case) as the plugin filename:
# Following classattributes have special meanings: 
#     "react_to"      ->   has to be a dict with keys out of these:
#                          ["private", "public", "dcc", "join", "leave",
#                          "server_connect", "enter_channel", "nick_change", "leave_channel",
#                          "public_command"]
#                     
#                          The values must be a compiled regular expression
#                          like returned from re.compile(). Use (?:\s+) to
#                          match whitespaces and use named groups so the resulting
#                          dict will be passed to react(). An example:
#                     
#                          re.compile("(?P<command>foo)(?:\s+)(?P<option>do|not|yes)(?:\s+)(?P<value>.+)") 
#                           
#                          The regular expressions for "private" and "public_command"
#                          only match against                      
#                    
#      "timers"         -> list of 2-tuples, register the provided method(s) for a timer based execution.
#                          You may register the method as string or as a callable object!
#                          [("methodname", timeout_in_seconds), (method_object, timeout_in_seconds)]
#
#      "author"         -> The plugin author
#                          
#      "provide"        -> A list of commands provided by this plugin, \
#                          private commands are marked with an underscore "_" in front
#
#      "aliases"        -> dict {str: str} mapping <alias> to a <provide-cmd>,
#                          the alias works exactly like the original, without 
#                          the need to add documentation for it.
#                          
#            
#      "config"         -> a dict providing configuration data for this plugin
#      "needed_configs" -> a list of mandatory configuration items to be found inside the config-dict
#
#      "doc"            -> a dictionary containing 2-tuples with the command as key to show help. (optional)
#                           only if plugin contains commands, all items from self.provide must be availible as keys here.
#
#      "final_setup"    -> a function being called before the boss...
#
#      "__doc__"        -> a docstring giving some basic information about this plugin            

class MyPlugin(AbstractPlugin):
    author = "myfancyname"

    react_to = {"public": re.compile(r"(?P<all>.+)"),
                "private": re.compile(r"(?P<all>.+)"),
                "join": re.compile(r"(?P<all>.+)"),
                "leave": re.compile(r"(?P<all>.+)"),
                "enter_channel": re.compile(r"(?P<all>.+)"),
                "leave_channel": re.compile(r"(?P<all>.+)"),
                "public_command": re.compile(r"(?P<arg1>.*)"),
                "private_command": re.compile(r"(?P<arg1>.*)"),
                "nick_change" : re.compile(r"(?P<old_nick>.+)")} 

    provide = ["mycommand", "myothercommand", "_myonlyprivateacceptedcommand"]

    def react(self, data):
        # data contains:
        # data.command       -> the used public_command or None
        # data.line          -> the regex-dictionary with the named groups
        # data.line_raw      -> the raw line that was sent (ONLY USE THIS IN ABSOLUTE EMERGENCIES) 
        # data.chan          -> the related channel if appropriate see class Channel in utils.py
        # dats.chan.users    -> a list of users in this channel, see class User in utils.py
        # data.user          -> the related user if appropriate see class User in utils.py
        # data.reaction_type -> the just handled reaction_type

        # some examples:
        # data.chan << "this text is send to the related channel"
        # data.chan << ["you can also pass a list of strings", "these are handled like separate lines"]
        #
        # data.user << "sends this text as /query to the user, not really nice, as this opens a new tab/window on most clients"
        # data.user << "sends this notice to the user - non intrusive as most clients show this in the active tab/window"
      
        #
        # return value is ignored!
        #

    doc = { "mycommand": ("mycommand [myarg]", "My Longer description"),
            "myothercommand": ("myothercommand", "Long FooBar desc and stuff"),
            "myonlyprivateacceptedcommand":("myonlyprivateacceptedcommand", "Note, the underscore is only used in provide")}

    __doc__ = "This plugin does something weird, and something strange"
