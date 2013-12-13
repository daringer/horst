#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from db.fields import IntegerField, StringField, DateTimeField, OneToManyRelation, OptionField, BooleanField
from db.baserecord import BaseRecord
from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime
from plugins.Stats import StatRecord


__metaclass__ = type

class UserRecord(BaseRecord):
    login = StringField(unique=True)
    password = StringField()
    register_date = DateTimeField(auto_now_add=True)
    last_login = DateTimeField(auto_now=True)
    nicks = OneToManyRelation(StatRecord)
    rank = OptionField(["VollNub", "ArschVomDienst", "Member", "Operator", "Admin"])
    
    # hostname => loginname
    _logged_in = {}    
            
    def promote(self, direction):
        """
        Degrade or promote UserRecord according to the 'direction' argument: 
        positive means promoting and a negativ value means a degrade
        """
        assert direction in [-1,1]
        new_idx = self.fields["rank"].options.index(self.rank)+direction
        if new_idx in [i for i, rankname in enumerate(self.fields["rank"].options)]:
            self.rank = self.fields["rank"].options[new_idx]
        self.save()
    
    @classmethod
    def logged_in(cls, user):
        """This one verifies, that the given utils::User() is a logged in User"""
        if user.hostname in cls._logged_in:
            return UserRecord.objects.get(login=cls._logged_in[user.hostname]) or False

    @classmethod
    def logging_in(cls, user, userrecord):
        """This should be called after a User is identified, thus logged in"""
        cls._logged_in[user.hostname] = userrecord.login
        
        
class UserAdmin(AbstractPlugin):
    author = "meissna"
    react_to = {"private": re.compile(r"(?:(?P<user>[\|\w_]+)\s(?P<uber_pass>.+))|(?P<pass>\w*)"),
                "public_command": re.compile(r"(?P<all>.*)"),
                "public": re.compile(r"(?P<all>.+)") } 
    
    provide = ["_identify", "_register", "_password", "giveop", "_promote", "_degrade", "status"]

    needed_configs = ["uber_pass"]
    
    def give_rights(self, urec, channel, nick):
        """Gives the rights defined in UserRecord::rank to 'user' in 'channel'"""
        flag = "+v" if urec.rank == "Member" else \
               "+o" if urec.rank == "Operator" else \
               "+a" if urec.rank == "Admin" else \
               "-aov"
        if flag == "-aov":
            channel << "Ne, du musst schon Member, Operator oder Admin sein, du bist nur: %s" % urec.rank
        channel.connection.send_raw("mode %s %s %s" % (channel.name, flag, nick))
 
    def react(self, data):
        nick, ur = data.user.name, None        
        if data.reaction_type == "public_command":
            ur = UserRecord.logged_in(data.user)
            if ur is None:
                data.chan << "Du bist nicht eingeloggt..."
            elif data.command == "giveop":
                self.give_rights(ur, data.chan, data.user.name)
            elif data.command == "status":
                data.chan << "Du bist ein: %s" % ur.rank
            else:
                data.chan << "Nein, ausser '%sgiveop' und '%sstatus' musst du das private machen" % (self.cp, self.cp)
        
        elif data.reaction_type == "public":
            # saving the relation between just used nickname and user-account
            # maybe cache this a bit, how about 'auto-caching' inside the "DatabaseAbstraction"
            ur = UserRecord.logged_in(data.user)
            if ur:
                sr = StatRecord.objects.get(nick=nick)
                if sr and not sr.userrecord:
                    sr.userrecord = ur
                    sr.save()
                    
        elif data.reaction_type == "private":
            # as we return if public, this is only executed on a private message
            if data.command == "identify":
                ur = UserRecord.objects.get(login=nick, password=data.line["pass"])
                if ur:
                    UserRecord.logging_in(data.user, ur)
                    data.user << "Du bist nu angemeldet"
                else:
                    if UserRecord.objects.get(login=nick):
                        data.user << "Falsches Passwort mein Freund, du willst doch nix böses oder?"
                    else:
                        data.user << "Habe deinen Nick nicht als Login in der Datenbank, mach mal 'nen 'register'"
                    
            elif data.command == "register":
                if UserRecord.objects.get(login=data.user.name):
                    data.user << "Der Loginname: '%s' ist bereits vergeben, wähle einen Anderen!!!" % nick
                else:
                    ur = UserRecord(login=nick, password=data.line["pass"])
                    data.user << "Du bist jetzt registriert! Logge ein mit: 'identify'"
                    
            elif data.command == "password":
                ur = self.logged_in(data.user)
                if ur:
                    ur.password = data.line["pass"]
                    data.user << "Passwort erfolgreich geändert!"
                else:
                    data.user << "Du bist nicht eingeloggt..."           
                    
            elif data.command in ["promote", "degrade"]:
                if data.line["uber_pass"] == self.config["uber_pass"]:
                    ur = UserRecord.objects.get(login=data.line["user"])
                    if ur:
                        ur.promote(-1 if data.command == "degrade" else 1)
                        data.user << "Der User: '%s' ist nun ein: '%s'" % (ur.login, ur.rank)
                    else:
                        data.user << "Der User: '%s' ist nicht vorhanden/registriert" % data.line["user"]
                else:
                    data.user << "Böse, böse falsches Passwort, willste ärger?"
            else:
                # we never should reach this
                assert False
        
            # if userrecord was touched, save it!
            if ur:
                ur.save()
    
    doc = { "identify" : ("identify <password>", "Logge dich bei mir ein und identifiziere dich mit deinem 'password'"),
            "register" : ("register <password>", "Registriere dich bei mir mit dem einem beliebigen 'password'"),
            "password" : ("password <new_password>", "Ändere dein Passwort zu 'new_password'"),
            "promote"  : ("promote <user> <uber_password>", "Befördere einen 'user' mit Hilfe des 'uber_password's"),
            "degrade"  : ("degrade <user> <uber_password>", "Degradiere einen 'user' mit Hilfe des 'uber_password's"),
            "giveop"   : ("giveop", "Ich gebe dir Operator Status falls du berechtigt bist"),
            "status"   : ("status", "Du wirst ganz schnell sehen wie wichtig du hier bist?!" ) }
    __doc__ = "Implementents a multi-level user management"
