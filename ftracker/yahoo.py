import ClientForm
import urllib2
import mechanize
import optparse
import sys
import datetime
from BeautifulSoup import BeautifulSoup
from ConfigParser import RawConfigParser

class YahooFFStats(object):

    cookies = False

    def __init__(self, yahooLogin, url):
        self.cj = mechanize.CookieJar()
        self.yahooLogin = yahooLogin
        self.url = url

    def genStats(self):
        self.cj = mechanize.CookieJar()
        if not self.cookies:
            initialRequest = mechanize.Request(self.url)
            response = mechanize.urlopen(initialRequest)
            forms = ClientForm.ParseResponse(response, backwards_compat=False)
            forms[0]['login'] = self.yahooLogin['user']
            forms[0]['passwd'] = self.yahooLogin['passwd']
            request2 = forms[0].click()
            response2 = mechanize.urlopen(request2)
            self.cj.extract_cookies(response, initialRequest)
            self.cookies = True
        request3 = mechanize.Request(self.url)
        self.cj.add_cookie_header(request3)
        response3 = mechanize.urlopen(request3)
        return self.readMainPage(response3.read())

    def getStandings(self, soup):
        standings = soup.find('table', id='standingstable')
        table_body = standings.tbody

        standingsList = []
        teamMapping = ['rank', 'team', 'w/l/t', 'winperc', 'pts',
                       'streak', 'waiver', 'moves']
        for fTeam in table_body.findAll('tr'):
            teamItem = {}
            itemIndex = 0
            for eStat in fTeam.findAll('td'):
                if eStat.get('class') == 'team':
                    name = eStat.first().string
                else:
                    name = eStat.string
                teamItem[teamMapping[itemIndex]] = name
                itemIndex += 1
            standingsList.append(teamItem)
        return standingsList

    def getScoreboard(self, soup):
        matchUpList = []
        scoreboard = soup.find('div', id='fantasytab')
        for matchUp in scoreboard.findAll("table"):
            matchUpDict = {}
            lastTeam = ""
            for eTd in matchUp.findAll('td'):
                if eTd.get('class') == 'pts':
                    matchUpDict[lastTeam] = eTd.string
                elif eTd.get('class') == 'first':
                    lastTeam = eTd.div.first().string
            matchUpList.append(matchUpDict)
        return matchUpList

    def readMainPage(self, data):
        soup = BeautifulSoup(data)
        standings = self.getStandings(soup)
        scoreboard = self.getScoreboard(soup)
        return (standings, scoreboard)
