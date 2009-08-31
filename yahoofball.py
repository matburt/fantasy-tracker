import ClientForm
import urllib2
import mechanize
import PyRSS2Gen
import optparse
import sys
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

    def readMainPage(self, data):
        soup = BeautifulSoup(data)
        standings = soup.find('table', id='standingstable')
        table_body = standings.tbody

        allTeamList = []
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
            allTeamList.append(teamItem)
        return allTeamList

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
    (options, args) = op.parse_args()

    if options.config is None:
        print("Configuration file required")
        sys.exit(1)

    config = getConfig(options.config)
    login = {'user': config.get('main','yahoologin'),
             'passwd': config.get('main','yahoopasswd')}
    fs = YahooFFStats(login, config.get('main','url'))

    allTeamList = fs.genStats()
    buffer = "Fantasy Football Standings:\n\n"
    for eTeam in allTeamList:
        buffer += "%s\n" % eTeam['team']
        buffer += "Rank: %s\n" % eTeam['rank']
        buffer += "Record: %s\n" % eTeam['w/l/t']
        buffer += "Win Percentage: %s\n" % eTeam['winperc']
        buffer += "Points: %s\n" % eTeam['pts']
        buffer += "Streak: %s\n\n" % eTeam['streak']
    print buffer

if __name__ == "__main__":
    main()
