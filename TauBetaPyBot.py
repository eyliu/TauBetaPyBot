#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name: TauBetaPyBot
# Summary: a bot for playing TBP Hunt (http://spider.eecs.umich.edu/~tbp/michelle/michelle.php)
# Author: Elson Liu
# Author-email: "Elson Liu" <eyliu.dev@umich.edu>
# License: BSD
# Requires: httplib2
# Requires: lxml


import optparse
import csv
import getpass
import httplib2
import lxml.html
import urllib
import re
import sys
import time

attributes = [
    "level",
    "experience",
    "neededexperience",
    "health",
    "maxhealth",
    "integrity",
    "maxintegrity",
    "gold"
]

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "TauBetaPyBot (Watson; JamesOS 1.0)",
    "Accept": "text/plain"
}

player = {}

state = {}

loggedin = False


def login():
    print "Logging in..."
    user = raw_input("Username: ")
    pw = getpass.getpass("Password: ")
    # user = "username"	# hardcode username and password for testing
    # pw = "password"
    body = {
        "loginS": "Login",
        "username": user,
        "password": pw
    }
    response, content = fetch_page(None,body)
    if "set-cookie" in response:
        headers["Cookie"] = response["set-cookie"]
    else:
        sys.exit()
    parse(content,None,body)
    loggedin = True


def explore():
    print "  Exploring..."
    query = {"action": "explore"}
    
    body = {"exploreS": "Explore"}
    print "    Stage 1: %s \t %s" % (query, body)
    response, content = fetch_page(query, body)
    wait_time = 8
    print "    Sleeping for %d seconds..." % wait_time
    time.sleep(wait_time)
    
    body = {"finishexploreS": "What Did I Find?!"}
    print "    Stage 2: %s \t %s" % (query, body)
    print ""
    response, content = fetch_page(query, body)
    parse(content, query)


def nap():
    print "  Napping..."
    query = {
        "action": "bullpen",
        "req": "nap"
    }
    response, content = fetch_page(query)
    parse(content,query)


def fight():
    print "  Fighting..."
    query = {
        "baction": "fight"
    }
    response, content = fetch_page(query)
    parse(content,query)


def flee():
    print "  Fleeing..."
    query = {
        "baction": "flee"
    }
    response, content = fetch_page(query)
    parse(content,query)


def donothing():
    print "  Doing nothing..."
    query = {
        "baction": "nothing"
    }
    response, content = fetch_page(query)
    parse(content,query)


def fetch_page(query,body=None):
    if query != None:
        url = "?".join([
            "http://spider.eecs.umich.edu/~tbp/michelle/michelle.php",
            urllib.urlencode(query)
        ])
    else:
        url = "http://spider.eecs.umich.edu/~tbp/michelle/michelle.php"
    http = httplib2.Http()
    if body != None:
        response, content = http.request(url, "POST", headers=headers,body=urllib.urlencode(body))
    else:
        response, content = http.request(url, "GET", headers=headers)
    if "set-cookie" in response:
        print "  Cookie: %s" % response["set-cookie"]
    return response, content

    
def parse(page,query,body=None):
    tree = lxml.html.document_fromstring(page)
    if body != None and "loginS" in body or query != None:
        print "    Scraping game state..."
        for attribute in attributes:
            search = "".join(["//span[@id='",attribute,"']"])
            player[attribute] = tree.xpath(search)[0].text_content().strip()
        print_status()
    if body != None and "finishexploreS" in body or query != None:
        print "    Scraping notification..."
        notification = tree.xpath("//p[@class='notify']")
        # print notification
        if notification != []:
            state["event"] = notification[0].text_content().strip()
            print "  Event: %s" % state["event"]


def print_status():
    level = " ".join(["Level:", player["level"]])
    experience = " ".join(["Experience:", " / ".join([player["experience"], player["neededexperience"]])])
    health = " ".join(["Health:", " / ".join([player["health"], player["maxhealth"]])])
    integrity = " ".join(["Integrity:", " / ".join([player["integrity"], player["maxintegrity"]])])
    gold = " ".join(["Gold:", player["gold"]])
    print "      " + "  ".join([level, experience, health, integrity, gold])


def main():
    wait_time = 0.5
    parser = optparse.OptionParser()
    parser.add_option('-n', action="store", dest="limit",
        help="number of iterations", default=1000)
    options, args = parser.parse_args()
    limit = int(options.limit)
    print "Number of rounds: %d" % limit
    login()
    for n in xrange(limit):
        print "\nROUND %d" % (n+1)
        explore()
        if state["event"].find("assailed") > -1:
            print "    Enemy detected."
            while float(player["health"]) / float(player["maxhealth"]) >= 0.6 and state["event"].find("defeated") < 0 and state["event"].find("Rebecca") < 0:
                percentage = float(player["health"]) / float(player["maxhealth"])
                print "    Health: %.2f" % percentage
                donothing()
                fight()
                print "    Sleeping for %.2f seconds..." % wait_time
                time.sleep(wait_time)
            if float(player["health"]) / float(player["maxhealth"]) < 0.6 or state["event"].find("Rebecca") > -1:
                donothing()
                flee()
        if float(player["health"]) / float(player["maxhealth"]) < 0.6:
            nap()


if __name__ == '__main__':
    main()