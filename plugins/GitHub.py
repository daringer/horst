#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time
import urllib
import urllib2
import json
import sys

from db import BaseRecord, IntegerField, StringField, FloatField, DateTimeField, BooleanField
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
    react_to = {"public": re.compile(r"(?P<action>add|del|list)(?:\s*)(?P<user>[^\s]*)(?:\s*)(?P<repo>[^\s]*)")} 
    provide = ["github"]
    timer = [("check_all_repos", 10)]

    def check_repo(self, user, repo):
        host = "api.github.com"
        args = urllib.urlencode({"page": "1", "per_page":"1"})
        url = "http://{}/repos/{}/{}/commits?{}".format(host, user, repo, args)
        r = urllib2.Request(url)
        with urllib2.urlopen(r) as fd:
            data = json.loads(fd.read())
        
        item = data[0]
        commit_sha = item["sha"]
        commit = item["commit"]
        
        print data

        obj = GithubRepository.objects.get(user=user, repo=repo, last_sha=commit_sha)
        if obj is None:
            comment = commit["message"]
            commiter = commit["commiter"]
            author = "{} <{}> at {}".format(commiter["author"], commiter["email"], commiter["date"])

            data.chan << "New commit on Github for user: {} in repo: {}".format(user, repo)
            data.chan << "Author: {}".format(author)
            data.chan << "Message: {}".format(comment)

    def check_all_repos(self):
        for item in GithubRepository.objects.all():
            self.check_repo(item.user, item.repo)

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
                    data.chan << "watching Github - user: {} repo: {}".format(user, repo)
        else:
            data.chan << "Please use one of these actions (add|del|list)!"

        return True

    doc = { "github": ("github <add|del|list> [reponame]", 
                       "Either add oder delete an github to monitor - or simply list all")}

    __doc__ = "This plugin provides a very simple monitor for Github repositories"
