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
#from utils import FancyDateTime, FancyTime, FancyFloat, FancyDate

__metaclass__ = type

class GithubRepository(BaseRecord):
    user = StringField(length=250)
    repo = StringField(length=250)
    last_sha = StringField(length=50)
    #last_check = DateTimeField(auto_now=True)

class Github(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command": re.compile(r"(?P<action>add|del|list)(?:\s*)(?P<user>[^\s]*)(?:\s*)(?P<repo>[^\s]*)")} 
    provide = ["github"]
    timer = [("check_all_repos", 300)]

    def check_repo(self, user, repo, horst_obj):
        host = "api.github.com"
        args = urllib.urlencode({"page": "1", "per_page": "1"})
        url = "https://{}/repos/{}/{}/commits?{}".format(host, user, repo, args)
        r = urllib2.Request(url)
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
		    chan << "New commit on Github for user: {} in repo: {}".format(user, repo)
		    chan << "Author: {}".format(author)
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
                data.chan << "Please provide two arguments (github user and repo name)"
                return 

            db_obj = GithubRepository.objects.get(user=user, repo=repo)
            
        if act == "add":
            if db_obj is not None:
                data.chan << "There already exists an entry for user: {} and repository: {} inside the database".\
                        format(user, repo)
            else:
                m = GithubRepository(user=user, repo=repo)
                m.save()
                data.chan << "added user: {} repo: {}".format(user, repo)

        elif act == "del":
            if db_obj is None:
                data.chan << "Could not find user: {} with repository: {} in database".format(user, repo)
            else:
                db_obj.destroy()
                data.chan << "deleted user: {} repo: {}".format(user, repo)

        elif act == "list":
            items = GithubRepository.objects.all()
            if len(items) == 0:
                data.chan << "No Github repositories registred yet!" 
            else:
                for item in items:
                    data.chan << "watching Github - user: {} repo: {}".format(item.user, item.repo)
        else:
            data.chan << "Please use one of these actions (add|del|list)!"

        return True

    doc = { "github": ("github <add <user> <reponame>>|<del <user> <reponame>>|<show [repo]>",
                       "Either add or delete a github repo to monitor - or simply list all")}

    __doc__ = "This plugin provides a very simple monitor for Github repositories"
