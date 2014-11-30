#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time
import urllib
import urllib2
import json
import sys

from db.fields import StringField, DateTimeField, BaseRecord
from abstract import AbstractPlugin

__metaclass__ = type

class GithubRepository(BaseRecord):
    user = StringField(size=250)
    repo = StringField(size=250)
    last_sha = StringField(size=50)

class Github(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command": re.compile(r"(?P<action>add|del|list)(?:\s*)(?P<user>[^\s]*)(?:\s*)(?P<repo>[^\s]*)")} 
    provide = ["github"]
    timer = [("check_all_repos", 150)]

    def check_repo(self, user, repo, horst_obj):
        host = "api.github.com"
        args = urllib.urlencode({
            "access_token": self.config["api_key"],
            "page": "1", 
            "per_page": "1"
        })
        url = "https://{}/repos/{}/{}/commits?{}".format(host, user, repo, args)
        
        r = urllib2.Request(url)
        r.add_header("User-Agent", "Python2.7 irc/github bot")
        r.add_header("Authorization","token {}".format(self.config["api_key"]))
        fd = urllib2.urlopen(r)
        
        item = json.loads(fd.read())[0]
        
        commit_sha = item["sha"]
        commit = item["commit"]
        
        obj = GithubRepository.objects.get(user=user, repo=repo)
        if obj.last_sha != commit_sha:
            comment = commit["message"]
            committer = commit["committer"]
            author = "{} <{}> at {}".format(committer["name"], committer["email"], committer["date"])
	    for chan in horst_obj.chans.values():
		    chan << "Whooot neuer Commit auf Github - User: {} in Repo: {}".format(user, repo)
		    chan << "Autor: {}".format(author)
		    chan << "Message: {}".format(comment)
            obj.last_sha = commit_sha
            obj.save()

    def check_all_repos(self, horst_obj):
        for item in GithubRepository.objects.all():
            self.check_repo(item.user, item.repo, horst_obj)

    def react(self, data):
        act, user, repo = data.line.get("action"), data.line.get("user"), data.line.get("repo")
        if act in ["add", "del"]:
            if user is None or repo is None:
                data.chan << "Maaan, einfach ZWEI Argumente mitgeben, <github-user> _und_ <github-repo>"
                return 

            db_obj = GithubRepository.objects.get(user=user, repo=repo)
            
        if act == "add":
            if db_obj is not None:
                data.chan << "Hierrrr, das Repo: {} von User: {} hab ich schon lange auf der watchlist!".format(repo, user)
            else:
                m = GithubRepository(user=user, repo=repo)
                m.save()
                data.chan << "Neues Github Repo is drin - User: {} Repo: {}".format(user, repo)

        elif act == "del":
            if db_obj is None:
                data.chan << "Kann den user: {} mit dem Repo: {} nicht finden! Typo???".format(user, repo)
            else:
                db_obj.destroy()
                data.chan << "Repo: {} wird nicht mehr beobachet (user: {})".format(repo, user)

        elif act == "list":
            items = GithubRepository.objects.all()
            if len(items) == 0:
                data.chan << "Kann leider nichts auflisten, noch keine Repositories eingetragen bei mir!" 
            else:
                for item in items:
                    data.chan << "Github - User: {} Repo: {}".format(item.user, item.repo)
        else:
            data.chan << "Oh man, DREI optionen gibt es, benutz auch nur die, echt eh... (add|del|list)"

        return True

    doc = { "github": ("github <add <user> <reponame>>|<del <user> <reponame>>|<list>",
                       "Either add or delete a github repo to monitor - or simply list all")}

    __doc__ = "This plugin provides a very simple monitor for Github repositories"
