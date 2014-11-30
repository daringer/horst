#-*- coding: utf-8 -*-

import sys
import os
import time
from random import random
from thread import start_new_thread
from itertools import chain as iter_chain

from irc.ircbot import SingleServerIRCBot
from irc.irclib import nm_to_n, nm_to_h, nm_to_uh

from utils import Channel, User, Data
import plugins

class BaseIRCBot(SingleServerIRCBot):
    
    # executed _ONCE_ on a successful server connection
    def custom_welcome_server(self, conn):
        """Server connect one-time hook to override"""
        pass
    
    # executed _ONCE_ on a successful channel join
    def custom_welcome_channel(self, channel, conn):
        """Channel join one-time hook to override"""
        pass
  
    def __init__(self, conf):
        self.nick = conf.nick
        self.chans = {}
        self.users = {}
        self.config = conf
        
        self.server = [(conf.server, conf.port)]

        self.command_prefix = conf.command_prefix
        self.used_plugins = conf.used_plugins

        self.timers = []

        # do some tweaking/flags-setting, if 'config.test_mode' is 'True'
        if self.config.test_mode:
            # force sql-debug
            self.config.db_debug = True
            # avoid spamming channels, use test_chan(s) provided
            self.config.chans = self.config.test_chans
            # apply special test-mode nickname
            self.nick = self.config.test_nick
            # start only the following plugins during 'test_mode'
            self.used_plugins = conf.test_plugins
        
        # init all plugins
        self.name2pmodule = {}
        self.name2pobj = {}
        self.known_commands = {}
        self.known_aliases = {}

        # apply init_plugin on all plugins
        map(self.init_plugin, (n for n in self.used_plugins \
                if n in plugins.available_plugins))

        # add aliases to self.known_commands
        for alias, target in self.known_aliases.items():
            self.known_commands[alias] = self.known_commands[target]


        # init database
        from db.core import Database
        Database.debug = self.config.db_debug
        Database().check_for_tables()

        # connect
        SingleServerIRCBot.__init__(self, self.server, self.nick, self.nick)

        # adding more global handlers
        self.ircobj.add_global_handler("whoisuser", self.on_whoisuser)
        self.ircobj.add_global_handler("kick", self.on_part)
        
        # there also is a self.channels, which we DON'T use - WHY? FIXME!
        for chan in conf.chans:
            self.chans[chan] = Channel(chan, self.connection)

    def init_plugin(self, name, relo=False):
        """Init one specific plugin ('name').
        reload == True, means that the module is just reloaded
        """
        
        # load module
        mod = reload(self.name2pmodule[name]) if relo \
                else __import__("plugins.{}".format(name), fromlist=name)
        # create instance
        obj = getattr(mod, name)(self)

        # maintain maps
        self.name2pmodule[name] = mod 
        self.name2pobj[name] = obj

        # command provider?
        if obj.provide is None:
            return 

        # loop for regular commands
        for cmd in obj.provide:
            self.known_commands[cmd if cmd[0] != "_" else cmd[1:]] = obj         
 
        # loop for aliases, if appropriate
        if obj.aliases is not None:
            for cmd, targ in obj.aliases.items():
                self.known_aliases[cmd] = targ
                self.known_commands[cmd] = obj

    def show_available_plugins(self):
        """Print all available plugins to stdout"""
    	print "Listing all available plugins: " 
        for p in plugins.available_plugins:
            print "- {}".format(p)

    def dispatch(self, data):
        """Command/event dispatcher.
        Handles all occuring events and dispatches it to the correct plugin to be handled
        """
        data.line_raw = unicode(data.line_raw, self.config.encoding)

        if data.reaction_type in ["public_command", "private"]: 
            line_raw = data.line_raw.strip().split(" ", 1)
            
            data.command = line_raw[0].strip()
            data.line_raw = line_raw[1] if len(line_raw) == 2 else ""
            
            if data.command in self.known_commands:
                self.execute_plugin(self.known_commands[data.command], data)
            elif data.reaction_type == "public_command":
                data.chan << "{} - I don't understand...".format(data.command)
            elif data.reaction_type == "private":
                data.user << "Stop nagging me with that shit..."
        else:
            for plug in self.name2pobj.values():
                self.execute_plugin(plug, data)
    
    def execute_plugin(self, plugin, data):
        """Ask plugin to handle the dispatched event/command and its data"""
        if self.config.threaded_plugins:
            start_new_thread(plugin.handle_input, (data, ))
        else:
            plugin.handle_input(data)

    def on_pubmsg(self, c, e):
        """Hook for public not-prefixed written text inside a channel.
        -> e.target() == channel 
        -> e.source() == nick!~user@hostname  
        """
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
        user, chan = self.users[nick], self.chans[e.target().lower()]
        
        line_raw = e.arguments()[0]
        data = Data(line_raw=line_raw, chan=chan, user=user)
        
        # execute plugins
        if line_raw.startswith(self.command_prefix):
            data.line_raw = data.line_raw[len(self.command_prefix):]
            data.reaction_type = "public_command"
            self.dispatch(data)
        else:
            data.reaction_type = "public"
            self.dispatch(data)
        
    def on_privmsg(self, c, e):
        """Hook for private message written to bot directly (/msg).
        --> e.target() == own_nick 
        --> e.source() == nick!~user@hostname
        """
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
        user, line_raw = self.users[nick], e.arguments()[0]
        
        data = Data(line_raw=line_raw, reaction_type="private", user=user)
        
        # execute plugins
        self.dispatch(data)
 
    def on_nick(self, c, e):
        """Hook for someone changing his nickname (/nick).
        --> e.target() == new_nick 
        --> e.source() == old_nick!~user@hostname
        """
        old_nick, new_nick = nm_to_n(e.source()), e.target()
        self.users[new_nick] = self.users[old_nick]
        del self.users[old_nick]
        self.users[new_nick].name = new_nick
    
        # execute plugins
        data = Data(line_raw=old_nick, reaction_type="nick_change", user=self.users[new_nick])
        self.dispatch(data)

    def on_quit(self, c, e):
        """Hook for an user quitting the server (/quit).
        --> e.source() == old_nick!~user@hostname
        """

        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
        user = self.users[nick]
        data = Data(line_raw=user.name, reaction_type="leave", chan=user.channels[0], user=user)

        for chan in user.channels:
            if user in chan.users:
                chan.users.remove(user)
        self.dispatch(data)
        
        del self.users[nick]
        
    def on_part(self, c, e):
        """Hook for an user leaving the channel (/part).
        --> e.target() == channel 
        --> e.source() == nick!~user@hostname
        """
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
            
        chan, user = self.chans[e.target().lower()], self.users[nick]

        if self.nick != user.name:
            if user in chan.users:
                chan.users.remove(user)
            if chan in self.chans:
                user.channels.remove(chan)
            
            data = Data(line_raw=user.name, reaction_type="leave", chan=chan, user=user)
            self.dispatch(data)
                                    
            if len(user.channels) == 0:
                del self.users[user.name]
        else:
            data = Data(line_raw=user.name, reaction_type="leave_channel", chan=chan, user=user)
            self.dispatch(data)
            
            del self.chans[chan.name]
            for u in self.users.values():
                if chan in u.channels: 
                    u.channels.remove(chan)

    def on_join(self, c, e):
        """Hook for someone joining the channel (/join).
        --> e.target() == channel 
        --> e.source() == nick!~user@hostname
        """
        nick, channame, hostname = nm_to_n(e.source()), e.target().lower(), nm_to_h(e.source())
        if self.nick != nick:
            chan = self.chans[channame]
            
            self.users[nick] = user = User(nick, hostname, self.connection) if \
                not nick in self.users else self.users[nick]
            
            user.channels += [chan]
            chan.users += [user]
            
            data = Data(line_raw=nick, reaction_type="join", chan=chan, user=user)
            self.dispatch(data)
        else:
            self.chans[channame] = chan = Channel(channame, self.connection)
            data = Data(line_raw=channame, reaction_type="enter_channel", chan=chan)            
            self.dispatch(data)
    
    def on_whoisuser(self, c, e):
        """Hook for an user sending a whois request (/whois).
        --> e.target() == which user has send the /whois 
        --> e.source() == irc-server url
        --> e.arguments()[0] == target nick 
        --> e.arguments()[1] == also nick? real name?
        --> e.arguments()[2] == full hostnmae
        """
        self.users[e.arguments()[0]].hostname = e.arguments()[2]
            
    def on_namreply(self, c, e):
        """Hook for ... I dunno exactly, called after on_join() (maybe nick-change-reply?).
        --> e.arguments()[0] == chantype in "@"->secret "*"->private "="->public 
        --> e.arguments()[1] == channelname 
        --> e.arguments()[2] == userlist as string whitespace seperated 
        """
        chan, nicknames = self.chans[e.arguments()[1].lower()], e.arguments()[2].split(" ")[:-1]
        for nick in nicknames:
            
            self.users[nick] = user = User(nick, None, self.connection) if \
                not nick in self.users else self.users[nick]
            
            user.channels += [chan]
            chan.users += [user]

        for u in chan.users:
            self.connection.whois([u.name])
            
    def on_welcome(self, c, e):
        """Hook for fresh server connect (/server).
        --> e.target() == own_nick # e.source() == serverurl
        """
        self.custom_welcome_server(self.connection)
        for chan in self.chans.keys():
            c.join(chan)
            self.custom_welcome_channel(chan, self.connection)
            
            # before entering next room waiting some random time 
            # to avoid (threading) race-conditions
            time.sleep(random() * 3.0)
            
    def on_disconnect(self, c, e):
        """Hook for disconnection from server, Seems not to work as intended! (/disconnect)."""
        while not c.is_connected():
            time.sleep(random() * 10.0)
            print "Disconnected - trying a reconnect!"
            self._connect()

    def on_nicknameinuse(self, c, e):
        """Hook for the chosen nickname being in use."""
        pass

    def start(self):
        """Entry method starting the threads and the main IRCBot instance"""
        # start threads
        if self.config.online_watchdog:
            start_new_thread(self.online_watchdog, ())

        start_new_thread(self.timer_thread, ())
        
        # call parent
        SingleServerIRCBot.start(self)

    def timer_thread(self):
        """Idle-looping thread for timer-based plugins, 
        register own timers simply inside the plugins!"""
        time.sleep(4)
        last_stamp = time.time()


        # self.timers contains a list of lists, each representing 
        # a specific timer task:
        # time_data = [ function to call, remaining time, timer timeout ]
        while True:
            try:
                time.sleep(0.5)
                stamp = time.time()
                for time_data in self.timers:
                    time_data[1] -= (stamp - last_stamp)
                    if time_data[1] < 0:
                        try:
                            time_data[0](self)
                        except Exception as e:
                            print e, str(e)
                            for n, chan in self.chans.items():
                                chan << "bad: timer callback method-call threw unexpected stuff..."

                        time_data[1] = int(time_data[2])
                        break
                last_stamp = stamp
            except Exception as e:
                print e, str(e)
                for n, chan in self.chans.items():
                    chan << "Wh00t, timer-thread crashed :(( !!!"
                    if not self.config.timer_crash_watchdog:
                        sys.exit(1)

        for n, chan in self.chans.items():
            chan << "What brought me here, baaaad, goin' to crash - bye bye..."
            sys.exit(1)
                
    def online_watchdog(self):
        """Watchdog to have second fallback (after on_disconnect) 
        to make sure the bot is always connected and inside the 
        designated channels. 
        ATTENTION: Currently not fully(?) working (FIXME).
        """
        
        while True:
            time.sleep(10)
            if not self.connection.is_connected():
                print "WATCHDOG trying (re)connect!"
                self._connect()
