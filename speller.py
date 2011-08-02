

import re
import cgi
import os
import urllib
import urllib2

from time import sleep

from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import backends
from google.appengine.api import logservice
logservice.AUTOFLUSH_EVERY_SECONDS = None
logservice.AUTOFLUSH_EVERY_BYTES = None
logservice.AUTOFLUSH_ENABLED = False

MONTH = "jun09"
NGRAM = "3"
PROB = "jp"
DATASET = "bing-body"
REQUESTURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/"+PROB+"?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"
GENURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/gen?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"


class lexicon0(db.Model):
    word = db.StringProperty(required = True)
    known = db.StringListProperty(indexed = False)

def lexicon_key(lexicon_name=None):
    return db.Key.from_path('lexicon0', lexicon_name or 'default')


def combination(wordlist,t):#argument t is to notify that it is the main query while using cobination for first time
    tempc = wordlist
    combinationqueryset = [listtostr(tempc[:i] +
                                     ["%s%s"%(tempc[i],tempc[i+1])] +
                                     tempc[i+2:] ) for i in range(0, len(tempc)-1)]
    cquery = listtostr(tempc)
    combinationqueryset.append(cquery)
    results = getjp1('',combinationqueryset,'')
    dictionary = dict(results)
    x = results.index((cquery,dictionary[cquery]))
    if (t==0): t = dictionary[cquery]
    if (results[0][0] == cquery):
        return (cquery,results[0][1],t)
    else:
        dictionary = dict(results)
        x = results.index((cquery,dictionary[cquery]))
        y = list()
        for i in range(x):
            y.append(combinationqueryset.index(results[i][0]))
        y.sort(reverse = True)
        cache = wordlist
        for z in y:
            cache[z] += cache[z+1]
            del cache[z+1]
        return combination(cache,t)
    
def spacesplits(wordlist):
    temps = wordlist
    query = listtostr(temps)
    strings = []
    for i in range(len(temps)):
        for y in range(1,len(temps[i])):
            strings.append(listtostr(temps[:i]+list([temps[i][:y],temps[i][y:]])+temps[i+1:]))
    strings.append(query)        
    results = getjp1('',strings,'')
    if (results[0][0] == query):
        return (query,results[0][1])
    else:
        return spacesplits(results[0][0].split())



def getjp(before,wordlist,after):               
    global REQUESTURL
    wordli = wordlist
    string = ''
    for x in wordli:
        string += before+" "+str(x)+" "+after+"\n"
    string = string.strip()
    jps = list()
    jps = urllib2.urlopen(
        urllib2.Request(REQUESTURL,str(string))).read().split()
    for i in range(len(jps)):
        jps[i] = float(jps[i])/(querylength(wordli[i]))
    dictionary = dict(zip(wordli,jps))
    return sorted(dictionary.iteritems(), key = lambda entity:entity[1], reverse = True)

def getjp1(before,wordlist,after):               
    global REQUESTURL
    string = ''
    for x in wordlist:
        string += before+" "+str(x)+" "+after+"\n"
    string = string.strip()
    jps = list()
    jps = urllib2.urlopen(
        urllib2.Request(REQUESTURL,str(string))).read().split()
    for i in range(len(jps)):
        jps[i] = float(jps[i])
    dictionary = dict(zip(wordlist,jps))
    return sorted(dictionary.iteritems(), key = lambda entity:entity[1], reverse = True)

class mainpage(webapp.RequestHandler):
    def get(self):
        global MONTH,DATASET,NGRAM,PROB,REQUESTURL,GENURL
        if len(self.request.get('m')):
            MONTH = str(self.request.get('m'))
        if len(self.request.get('d')):
            DATASET = str(self.request.get('d'))
        if len(self.request.get('ng')):
            NGRAM = str(self.request.get('ng'))
        if len(self.request.get('pp')):
            PROB = str(self.request.get('pp'))
        REQUESTURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/"+PROB+"?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"        
        GENURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/gen?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"
        query = str(self.request.get('q'))
        wordlist = query.strip().split()
        dictionary = dict()
        try:
            cquery = combination(wordlist,0)[0]
        except:
            cquery = query
        try:
            wordlist = query.strip().split()
            squery = spacesplits(wordlist)[0]
        except:
            squery = query
        try: dictionary.update(getdictionary(wordlist))
        except:
            dictionary.update({query:0})
        try:
            if (query != cquery): dictionary.update(getdictionary(cquery.split()))
        except: dictionary.update({cquery:0})
        try:
            if (query != squery): dictionary.update(getdictionary(squery.split()))
        except: dictionary.update({squery:0})
        finallist = dictionary.keys()
        self.response.headers['Content-Type'] = 'text/plain'
        try:
            result = getjp('',finallist,'')
            final = list()
            for i in range(len(result)):
                final.append(10**((result[i][1])))
            printresult = normalize(final)
            for i in range(len(printresult)):
                self.response.out.write(str(result[i][0])+"\t"+printresult[i]+"\n")
        except:
            self.response.out.write(query+"\t"+str(1))
        

        
class maintest(webapp.RequestHandler):
    def get(self):
        global MONTH,DATASET,NGRAM,PROB,REQUESTURL,GENURL
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(REQUESTURL+"\n")
        self.response.out.write(GENURL)
            


def getdictionary(wordelist):
    global MONTH,DATASET,NGRAM,PROB
    dictionaryy = dict()
    rpcs = []
    for i in range(len(wordelist)):
        if i<3: t=0
        else: t = i-3
        form_fields = {
            "word": wordelist[i],
            "before": listtostr(wordelist[t:i]),
            "after": listtostr(wordelist[i+1:i+4]),
            "m": MONTH,
            "d": DATASET,
            "ng": NGRAM,
            "pp": PROB
            }
        formdata = urllib.urlencode(form_fields)
        rpc = urlfetch.create_rpc()
        url = "http://timetest.forbackend.appspot.com/wordspellcheck"
        #rpc.callback = create_callback(rpc)
        urlfetch.make_fetch_call(rpc,
                                     url,
                                     payload = formdata,
                                     method = urlfetch.POST)
        rpcs.append(rpc)
    resultts = list()
    for rpc in rpcs:
        result = rpc.get_result()
        resultts.append(result.content)
    #self.response.out.write(results)
    #self.response.out.write(wordee)
    dictionaryy[listtostr(wordelist)] = 0
    for i in range(len(wordelist)):
        if resultts[i] == wordelist[i]: continue
        else:
            for j in range(i,len(wordelist)+1):
                pp = listtostr(wordelist[:i]+resultts[i:j]+wordelist[j:])
                dictionaryy[pp] = 0
    return dictionaryy

                
class splittest(webapp.RequestHandler):
    def get(self):
        query = self.request.get('q')
        wordlist = query.split()
        splitted = combination(wordlist,0)
        self.response.out.write(splitted)

def querylength(query):
    liste = query.split()
    counte = 0
    for x in liste:
        if len(x)>1: counte += 1
    if counte == 0: return 1
    else: return counte

def listtostr(wordlist):
    string = ''
    for word in wordlist:
        string += word+" "
    string = string.strip()
    return string
#def create_callback(rpc):
    
def normalize(problist):
    tot = 0
    for x in problist:
        tot += x
    returnlist = list()
    for i in range(len(problist)):
        returnlist.append(str(round((problist[i]/tot),3)))
    return returnlist
        
application = webapp.WSGIApplication([
    ('/mainpage',maintest),#### the main speller is in main page web handler as i submitted maintest as the official submission i changed this
    ('/maintest',mainpage),
    ('/split',splittest)],
                                     debug = True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
