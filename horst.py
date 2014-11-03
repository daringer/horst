#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import time

# basebot to derive from 
from basebot import BaseIRCBot

# configuration settings
from config import Config
   
class Horst(BaseIRCBot):
    """This is the Main Class, 
    by deriving from 'BaseIRCBot' an arbitrary number of bots may be spawned.
    Only two methods are overloaded here:
    - custom_welcome_server()   ->   send /oper cmd on server connect to get (global) "oper"-status
    - custom_welcome_channel()  ->   send /mode cmd on channel join to get (local) "operator"-status
    """
    def custom_welcome_server(self, conn):
        conn.send_raw(Config.server_welcome_cmd. \
                format(user=self.nick, oper_pass=Config.oper_password))
        
    def custom_welcome_channel(self, channel, conn):
        conn.send_raw(Config.channel_welcome_cmd. \
                format(chan=channel, user=self.nick))

###############################################################################
##### starting here!

if len(sys.argv) > 1 and sys.argv[1] in ["--list-plugins", "-l"]:
    bot = Horst(Config)
    bot.show_available_plugins()
else:

    # most primitive arg-parsing possible (TODO/FIXME)
    while len(sys.argv) > 1:
        if sys.argv[1] in ["--sql-debug", "-d"]:
            Config.db_debug = True
            del sys.argv[1]
        
        elif sys.argv[1] in ["--testing", "-t"]:
            Config.test_mode = True
            del sys.argv[1]
        
        elif sys.argv[1] in ["--crash-watchdog", "-c"]:
            Config.crash_watchdog = True
            del sys.argv[1]
        
        elif sys.argv[1] in ["--no-crash-watchdog", "-n"]:
            Config.crash_watchdog = False
            del sys.argv[1]

        else:
            print "UNKNOWN argument passed: {}".format(sys.argv[1])
            print "exiting..."
            sys.exit(1)

    #################################
    # crash watchdog is here
    if Config.crash_watchdog:
        while True:
            try:
                bot = Horst(Config)
                bot.start()
            except Exception as e:
                print "Catched un-catched exception ..."
                print "MEANS WE CRASHED - exception following:"
                print type(e), e 
                print "msg: {}".format(e.message)

                import traceback as t
                t.print_stack()

    #################################
    # starting without crash watchdog
    else:
        bot = Horst(Config)
        bot.start()





