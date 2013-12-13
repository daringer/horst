#-*- coding: utf-8 -*-

import sys, os, time

from thread import start_new_thread

from irc.ircbot import SingleServerIRCBot
from irc.irclib import nm_to_n, nm_to_h, nm_to_uh

# horst plugins and utils
from utils import Channel, User, Data
import plugins

class BaseIRCBot(SingleServerIRCBot):
    # the following methods can be overridden to implement features based on these hooks
    def custom_welcome_server(self, conn):              pass
    def custom_welcome_channel(self, channel, conn):    pass
  
    def __init__(self, conf):
        self.nick = conf.nick
        self.chans = {}
        self.users = {}
	self.config = conf
        
        self.server = [(conf.server, conf.port)]

        self.command_prefix = conf.command_prefix
        self.used_plugins = conf.used_plugins
        
        #self.plugins = []
        #for use in self.used_plugins:
        #    if use in plugins.available_plugins:
        #        load = __import__("plugins.%s" % use, fromlist=use)
        #        self.plugins.append(getattr(load,use)(self))
        self.plugins = [getattr(__import__("plugins.%s" % use, fromlist=use), use)(self) \
                            for use in self.used_plugins \
                                if use in plugins.available_plugins]

        #self.known_commands = {}
        #for plug in self.plugins:
        #    if plug.provide:
        #        for provide in plug.provide:            
        #           self.known_commands[provide if not provide.startswith("_") else provide[1:]] = plug       
        self.known_commands = dict(reduce(lambda a,b: a+b, 
                                ([(provide if not provide.startswith("_") else provide[1:], plug) \
                                    for provide in plug.provide ] \
                                        for plug in self.plugins if plug.provide )))    
        
        #self.known_private_commands = dict(reduce(lambda a,b: a+b, 
        #                        ([(provide, plug) for provide in plug.provide if provide.startswith("_")] 
        #                          for plug in self.plugins if plug.provide )))    
        
        # init database
        from db.core import Database
        Database().check_for_tables()

        # connect
        SingleServerIRCBot.__init__(self, self.server, self.nick, self.nick)

        # adding more global handlers
        self.ircobj.add_global_handler("whoisuser", self.on_whoisuser)
        self.ircobj.add_global_handler("kick", self.on_part)
        
        # there also is a self.channels, which we DON'T use - WHY? FIXME!
        for chan in conf.chans:
            self.chans[chan] = Channel(chan, self.connection)
    
    def show_available_plugins(self):
    	print "[i] Listing all available plugins: " 
        for p in plugins.available_plugins:
            print "  [i] {}".format(p)
            #print "  [i] {} ({})".format(p, self.plugins[p].__doc__)
	print

    def execute_plugins(self, data):
        if data.reaction_type in ["public_command", "private"]:
            line_raw = data.line_raw.strip().split(" ", 1)
            
            data.command = line_raw[0].strip()
            data.line_raw = line_raw[1] if len(line_raw) == 2 else ""
            
            if data.command in self.known_commands:
                start_new_thread(self.known_commands[data.command].handle_input, (data,))
            elif data.reaction_type == "public_command":
                data.chan << "%s - I don't understand..." % data.command
            elif data.reaction_type == "private":
                data.user << "Stop nagging me with that shit..."
        else:
            for plug in self.plugins:
                start_new_thread(plug.handle_input, (data,))
            
    # someone writing in channel
    # e.target() == channel # e.source() == nick!~user@hostname
    def on_pubmsg(self, c, e):
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
            self.execute_plugins(data)
        else:
            data.reaction_type = "public"
            self.execute_plugins(data)
        
    # someone sending a private msg
    # e.target() == own_nick # e.source() == nick!~user@hostname
    def on_privmsg(self, c, e):
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
        user, line_raw = self.users[nick], e.arguments()[0]
        
        data = Data(line_raw=line_raw, reaction_type="private", user=user)
        
        # execute plugins
        self.execute_plugins(data)
 
    # someone changing nick
    # e.target() == new_nick # e.source() == old_nick!~user@hostname
    def on_nick(self, c, e):
        old_nick, new_nick = nm_to_n(e.source()), e.target()
        self.users[new_nick] = self.users[old_nick]
        del self.users[old_nick]
        self.users[new_nick].name = new_nick
    
        # execute plugins
        data = Data(line_raw=old_nick, reaction_type="nick_change", user=self.users[new_nick])
        self.execute_plugins(data)

    # for quitting ppl behave like they just /part
    def on_quit(self, c, e):
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
        user = self.users[nick]
        data = Data(line_raw=user.name, reaction_type="leave", chan=user.channels[0], user=user)

        for chan in user.channels:
            if user in chan.users:
                chan.users.remove(user)
        self.execute_plugins(data)
        
        del self.users[nick]
        
    # someone leaving channel
    # e.target() == channel # e.source() == nick!~user@hostname
    def on_part(self, c, e):
        nick, hostname = nm_to_n(e.source()), nm_to_h(e.source())
        if not nick in self.users:
            self.users[nick] = User(nick, hostname, self.connection)
            
        chan, user = self.chans[e.target().lower()], self.users[nick]
        if self.nick != user.name:
            # execute plugins
            if user in chan.users:
                chan.users.remove(user)
            if chan in self.chans:
                user.channels.remove(chan)
            
            data = Data(line_raw=user.name, reaction_type="leave", chan=chan, user=user)
            self.execute_plugins(data)
                                    
            if len(user.channels) == 0:
                del self.users[user.name]
        else:
            data = Data(line_raw=user.name, reaction_type="leave_channel", chan=chan, user=user)
            self.execute_plugins(data)
            
            del self.chans[chan.name]
            for u in self.users.values():
                if chan in u.channels: 
                    u.channels.remove(chan)

    # joining some channel
    # e.target() == channel # e.source() == nick!~user@hostname
    def on_join(self, c, e):
        nick, channame, hostname = nm_to_n(e.source()), e.target().lower(), nm_to_h(e.source())
        if self.nick != nick:
            chan = self.chans[channame]
            
            self.users[nick] = user = User(nick, hostname, self.connection) if \
                not nick in self.users else self.users[nick]
            
            user.channels += [chan]
            chan.users += [user]
            
            # execute plugins
            data = Data(line_raw=nick, reaction_type="join", chan=chan, user=user)
            self.execute_plugins(data)
        else:
            self.chans[channame] = chan = Channel(channame, self.connection)
            data = Data(line_raw=channame, reaction_type="enter_channel", chan=chan)            
            self.execute_plugins(data)
    
    # whois for user 
    # e.target() == which user has send the /whois  # e.source() == irc-server url
    # e.arguments()[0] == target nick
    # e.arguments()[1] == also nick? real name?
    # e.arguments()[2] == full hostname
    def on_whoisuser(self, c, e):
        self.users[e.arguments()[0]].hostname = e.arguments()[2]
            
    # namreply ???? whatever this is, this is called after on_join() into a channel
    # e.arguments()[0] == chantype in "@"->secret "*"->private "="->public
    # e.arguments()[1] == channelname
    # e.arguments()[2] == userlist as string whitespace seperated
    def on_namreply(self, c, e):
        chan, nicknames = self.chans[e.arguments()[1].lower()], e.arguments()[2].split(" ")[:-1]
        for nick in nicknames:
            
            self.users[nick] = user = User(nick, None, self.connection) if \
                not nick in self.users else self.users[nick]
            
            user.channels += [chan]
            chan.users += [user]

        for u in chan.users:
            self.connection.whois([u.name])
            
    # connected to server
    # e.target() == own_nick # e.source() == serverurl
    def on_welcome(self, c, e):
        self.custom_welcome_server(self.connection)
        for chan in self.chans.keys():
            c.join(chan)
            self.custom_welcome_channel(chan, self.connection)
            
    # do something on disconnect
    def on_disconnect(self, c, e):
    	while not c.is_connected():
	    time.sleep(10)
	    print "disconnected - trying reconnect!"
	    self._connect()

    
    # do something if nick in use
    def on_nicknameinuse(self, c, e):
        # todo: change nickname but how?!
        pass

    def start_online_watchdog(self):
	from thread import start_new_thread
	start_new_thread(self.online_watchdog, ())

    # online watchdog
    def online_watchdog(self):
	while True:
            time.sleep(10)
            if not self.connection.is_connected():
                print "WATCHDOG connect!"
                self._connect()


            

