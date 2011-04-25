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

eattributes = [
    "enemycurrenthp",
    "enemymaxhp"
]

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "TauBetaPyBot (Watson; JamesOS 1.0)",
    "Accept": "text/plain"
}

player = {}

enemy = {}

state = {}

loggedin = False

csvfile = None

def enable_colors(c):
    global COLOR_RED
    global COLOR_GREEN
    global COLOR_YELLOW
    global COLOR_WHITE
    global COLOR_NONE

    if c:
        COLOR_RED   ="\x1b[1;31m"
        COLOR_GREEN ="\x1b[1;32m"
        COLOR_YELLOW="\x1b[1;33m"
        COLOR_WHITE ="\x1b[1;37m"
        COLOR_NONE  ="\x1b[m"
    else:
        COLOR_RED   =""
        COLOR_GREEN =""
        COLOR_YELLOW=""
        COLOR_WHITE =""
        COLOR_NONE  =""

def cprint(c, txt):
    print "%s%s%s" % (c, txt, COLOR_NONE)

def csvhead():
    global csvfile

    if csvfile is None:
        csvfile = file("stats-%d.csv" % int(time.time()), "w")

    a = ["Date",]
    a.extend(attributes)
    a.extend(eattributes)
    csvfile.write(",".join(a) + "\n")

def csvstats():
    a = [str(time.time()),]
    for k in attributes:
        a.append(str(player.get(k,"NA")))
    for k in eattributes:
        a.append(str(enemy.get(k,"NA")))
    csvfile.write(",".join(a) + "\n")
    csvfile.flush()

def login():
    cprint(COLOR_GREEN, "logging in...")
    user = raw_input("Username: ")
    pw = getpass.getpass("Password: ")
    # user = "username" # hardcode username and password for testing
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
    cprint(COLOR_GREEN, "exploring...")
    query = {"action": "explore"}
    
    body = {"exploreS": "Explore"}
    response, content = fetch_page(query, body)

    time.sleep(8)
    
    body = {"finishexploreS": "What Did I Find?!"}
    response, content = fetch_page(query, body)
    parse(content, query)


def nap():
    cprint(COLOR_GREEN, "napping...")
    query = {
        "action": "bullpen",
        "req": "nap"
    }
    response, content = fetch_page(query)
    parse(content,query)


def fight():
    cprint(COLOR_GREEN, "fighting...")
    query = {
        "baction": "fight"
    }
    response, content = fetch_page(query)
    parse(content,query)


def flee():
    cprint(COLOR_GREEN, "fleeing...")
    query = {
        "baction": "flee"
    }
    response, content = fetch_page(query)
    parse(content,query)


def withstand():
    cprint(COLOR_GREEN, "casting withstand...")
    query = {
        "baction": "Withstand"
    }
    response, content = fetch_page(query)
    parse(content,query)


def donothing():
    cprint(COLOR_GREEN, "doing nothing...")
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
        response, content = http.request(url, "POST", headers=headers,
                                         body=urllib.urlencode(body))
    else:
        response, content = http.request(url, "GET", headers=headers)
    if "set-cookie" in response:
        print "Cookie: %s" % response["set-cookie"]
    return response, content

    
def parse(page,query,body=None):
    tree = lxml.html.document_fromstring(page)
    if body != None and "loginS" in body or query != None:
        for attribute in attributes:
            search = "".join(["//span[@id='",attribute,"']"])
            player[attribute] = float(tree.xpath(search)[0].text_content().strip())
    if body != None and "finishexploreS" in body or query != None:
        notification = tree.xpath("//p[@class='notify']")
        # print notification
        if notification != []:
            state["event"] = notification[0].text_content().strip()
    if query != None and "baction" in query:
        for attribute in eattributes:
            search = "".join(["//span[@id='",attribute,"']"])
            results = tree.xpath(search)
            if results != []:
                enemy[attribute] = results[0].text_content().strip()
        bnotifications = tree.xpath("//p[@class='fightnotify']")
        mnotifications = tree.xpath("//p[@class='enchantnotify']")
        bevents = []
        mevents = []
        for bnotify in bnotifications:
            bevent = bnotify.text_content().strip()
            print "  Battle event: %s" % bevent
            bevents.append(bevent)
        for mnotify in mnotifications:
            mevent = mnotify.text_content().strip()
            print "  Magical event: %s" % mevent
            mevents.append(mevent)
        state["bevents"] = bevents
        state["mevents"] = mevents

    if "event" in state:
        cprint(COLOR_YELLOW, state["event"])
    print_status()


def print_status():
    _l    = player["level"]
    _xp   = player["experience"]
    _nxp  = player["neededexperience"]
    _hp   = player["health"]
    _mhp  = player["maxhealth"]
    _int  = player["integrity"]
    _mint = player["maxintegrity"]
    _gold = player["gold"]

    cprint(COLOR_NONE, "level %4d, xp %d / %d, health %d / %d (%d%%), integrity %d / %d, gold %d" %
           (_l, _xp, _nxp, _hp, _mhp, int(100*_hp/_mhp), _int, _mint, _gold,))
    csvstats()

def main():
    wait_time = 0.5
    parser = optparse.OptionParser()
    parser.add_option('-n', action="store", dest="limit",
        help="number of iterations", default=1000)
    parser.add_option('-c', action="store_true", dest="color",
        help="enable ANSI color escape codes", default=False)
    options, args = parser.parse_args()
    limit = int(options.limit)
    enable_colors(bool(options.color))

    csvhead()
    print "Number of rounds: %d" % limit
    login()
    for n in xrange(limit):
        cprint(COLOR_WHITE,"\nROUND %d" % (n+1,))
        explore()

        if "event" in state and state["event"].find("assailed") > -1:
            battle_round = 1
            aim_round = -1
            reload_round = -1
            while float(player["health"]) / float(player["maxhealth"]) > 0.6 and \
                  state["event"].find("defeated") < 0 and \
                  state["event"].find("Rebecca") < 0 and \
                  state["event"].find("Launcher") < 0:
                percentage = player["health"] / player["maxhealth"]
                
                if "bevents" in state:
                    for bevent in state["bevents"]:
                        if bevent.find("taking aim") > -1:
                            aim_round = battle_round
                            cprint(COLOR_RED,"Danger, Will Robinson!  Rogue Nerf Bow and Arrow is taking aim!")

                if battle_round == aim_round:
                    withstand()
                else:
                    donothing()
                    fight()

                time.sleep(wait_time)
                battle_round += 1

            if float(player["health"]) / float(player["maxhealth"]) <= 0.6 or \
               state["event"].find("Rebecca") > -1 or \
               state["event"].find("Launcher") > -1:
                donothing()
                flee()

        if float(player["health"]) / float(player["maxhealth"]) <= 0.6 or \
           float(player["integrity"]) / float(player["maxintegrity"]) <= 0.8:
            nap()

        if int(player["health"]) <= 0:
            death_timeout = 125
            cprint(COLOR_RED, "TauBetaPyBot has died! :-(  Sleeping for %d seconds..." % (death_timeout,))
            time.sleep(death_timeout)
            nap()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cprint(COLOR_RED, "Bye, bye.")
