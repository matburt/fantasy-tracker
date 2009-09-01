import ClientForm
import urllib2
import mechanize
import PyRSS2Gen
import optparse
import sys
import datetime
from BeautifulSoup import BeautifulSoup
from ConfigParser import RawConfigParser

class FFStatPublisher(object):

    def __init__(self, destination,
                 docTitle='Fantasy Football Stats',
                 docLink=None):
        self.destination = destination
        self.rssGen = PyRSS2Gen.RSS2(
            title = docTitle,
            link = docLink,
            description = docTitle,
            lastBuildDate = datetime.datetime.now())

    def createItem(self, itemDict):
        item = PyRSS2Gen.RSSItem(
            title = itemDict["title"],
            description = itemDict["content"],
            pubDate = datetime.datetime.now())
        self.rssGen.items.append(item)

    def addItems(self, itemList):
        self.rssGen.items.append(itemList)

    def write(self):
        self.rssGen.write_xml(open(self.destination, "w"))

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
        scoreboard = soup.find('div', id='fantasytab')#, class='scoreboard')
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


def getConfig(path):
    rc = RawConfigParser()
    if path not in rc.read(path):
        print("Invalid Configuration File")
        sys.exit(1)
    return rc

def main():
    op = optparse.OptionParser()
    op.add_option("-c", "--config", dest="config",
                  help="configuration file")
    op.add_option("-o", "--output", dest="output")
    (options, args) = op.parse_args()

    if options.config is None:
        print("Configuration file required")
        sys.exit(1)

    config = getConfig(options.config)
    login = {'user': config.get('main','yahoologin'),
             'passwd': config.get('main','yahoopasswd')}
    fs = YahooFFStats(login, config.get('main','url'))
    pub = FFStatPublisher(options.output,
                          config.get('rss', 'title'),
                          config.get('rss', 'url'))

    standings, scoreboard = fs.genStats()
    contentBuffer = "Fantasy Football Standings:\n\n"
    for eTeam in standings:
        contentBuffer += "%s\n" % eTeam['team']
        contentBuffer += "Rank: %s\n" % eTeam['rank']
        contentBuffer += "Record: %s\n" % eTeam['w/l/t']
        contentBuffer += "Win Percentage: %s\n" % eTeam['winperc']
        contentBuffer += "Points: %s\n" % eTeam['pts']
        contentBuffer += "Streak: %s\n\n" % eTeam['streak']
    pub.createItem({"title": "FF Standings %s" %
                    datetime.datetime.now().isoformat(),
                    "content": contentBuffer})

    scoreBuffer = "Fantasy Football Scoreboard:\n\n"
    for matchUp in scoreboard:
        for team in matchUp:
            scoreBuffer += "%s: %s\nvs.\n" % (team, matchUp[team])
        scoreBuffer = scoreBuffer[:-4] + "\n"
    pub.createItem({"title": "FF Scoreboard %s" %
                    datetime.datetime.now().isoformat(),
                    "content": scoreBuffer})

    pub.write()
    print contentBuffer
    print scoreBuffer

if __name__ == "__main__":
    main()
