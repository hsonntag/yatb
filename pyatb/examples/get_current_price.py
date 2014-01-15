#!/usr/bin/python
#examples/get_current_price.py
import datetime
import decimal
import json
import httplib

"""
Poll the current NMC/BTC
=====
Use API
"""

btce_domain = "btc-e.com"

all_pairs = ("btc_usd", "btc_rur", "btc_eur", "ltc_btc", "ltc_usd",
             "ltc_rur", "ltc_eur", "nmc_btc", "nmc_usd", "nvc_btc",
             "nvc_usd", "usd_rur", "eur_usd", "trc_btc", "ppc_btc",
             "ppc_usd", "ftc_btc", "xpm_btc")

class BTCEConnection:
    def __init__(self, timeout=30):
        self.conn = httplib.HTTPSConnection(btce_domain, timeout=timeout)
        self.cookie = None

    def close(self):
        self.conn.close()

    def getCookie(self):
        self.cookie = ""

        self.conn.request("GET", '/')
        response = self.conn.getresponse()

        setCookieHeader = response.getheader("Set-Cookie")
        match = HEADER_COOKIE_RE.search(setCookieHeader)
        if match:
            self.cookie = "__cfduid=" + match.group(1)

        match = BODY_COOKIE_RE.search(response.read())
        if match:
            if self.cookie != "":
                self.cookie += '; '
            self.cookie += "a=" + match.group(1)

    def makeRequest(self, url, extra_headers=None, params="", with_cookie=False):
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        if extra_headers is not None:
            headers.update(extra_headers)

        if with_cookie:
            if self.cookie is None:
                self.getCookie()

            headers.update({"Cookie": self.cookie})

        self.conn.request("POST", url, params, headers)
        response = self.conn.getresponse().read()

        return response

    def makeJSONRequest(self, url, extra_headers=None, params=""):
        response = self.makeRequest(url, extra_headers, params)
        return parseJSONResponse(response)

class Ticker(object):
    __slots__ = ('high', 'low', 'avg', 'vol', 'vol_cur', 'last', 'buy', 'sell', 'updated', 'server_time')

    def __init__(self, **kwargs):
        for s in Ticker.__slots__:
            setattr(self, s, kwargs.get(s))

        self.updated = datetime.datetime.fromtimestamp(self.updated)
        self.server_time = datetime.datetime.fromtimestamp(self.server_time)

    def __getstate__(self):
        return dict((k, getattr(self, k)) for k in Ticker.__slots__)

    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)

def parseJSONResponse(response):
    def parse_decimal(var):
        return decimal.Decimal(var)

    try:
        r = json.loads(response, parse_float=parse_decimal,
                       parse_int=parse_decimal)
    except Exception as e:
        msg = "Error while attempting to parse JSON response:"\
              " %s\nResponse:\n%r" % (e, response)
        raise Exception(msg)

    return r

def validatePair(pair):
    if pair not in all_pairs:
        if "_" in pair:
            a, b = pair.split("_")
            swapped_pair = "%s_%s" % (b, a)
            if swapped_pair in all_pairs:
                msg = "Unrecognized pair: %r (did you mean %s?)"
                msg = msg % (pair, swapped_pair)
                raise Exception(msg)
        raise Exception("Unrecognized pair: %r" % pair)

            
def getTicker(pair, connection=None):
    '''Retrieve the ticker for the given pair.  Returns a Ticker instance.'''

    validatePair(pair)

    if connection is None:
        connection = BTCEConnection()

    response = connection.makeJSONRequest("/api/2/%s/ticker" % pair)

    if type(response) is not dict:
        raise Exception("The response is a %r, not a dict." % type(response))

    return Ticker(**response[u'ticker'])

if __name__ == '__main__':
    ticker = getTicker('nmc_btc')
    print str(ticker.avg) + 'BTC per NMC'