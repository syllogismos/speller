

## gets a post request to send alternate
## word suggestions of given word with before and after strings
## along with probabilities, all (before,after,word are strings)

import os
import cgi
import urllib2
import urllib
import re
import letterprobs
import difflib
import speller

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import logservice

logservice.AUTOFLUSH_EVERY_BYTES = None
logservice.AUTOFLUSH_EVERY_SECONDS = None
logservice.AUTOFLUSH_EVERY_LINES = 100
logservice.AUTOFLUSH_ENABLED = False

#GENURL = speller.GENURL
#REQUESTURL = speller.REQUESTURL

MONTH = "jun09"
NGRAM = "3"
PROB = "jp"
DATASET = "bing-body"
REQUESTURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/"+PROB+"?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"
GENURL = "http://web-ngram.research.microsoft.com/rest/lookup.svc/"+DATASET+"/"+MONTH+"/"+NGRAM+"/gen?u=888b8bfe-a203-43c6-a303-ab8e8d47b38e"


def edits(word):
    alphabet = 'abcdedfghijklmnopqrstuvwxyz'
    suffixes = ['ia', 'less', 'ite', 'bound', 'meter', 'holic', ' s', 'cy', 'ality', 'ity', 'gry', 'ose', 'hood', 'ial', 'ian', 'ty', 'ment', 'ier', 'ergy', 'ectomy', 'wright', 'ade', 'acious', 'th', 'ed', 'escent', 'scope', 'ent', 'cycle', 'tude', 'city', 'ic', 'ly', 'ant', 'ium', 'cide', 'iate', 'phone', 'ical', 'osis', 'ling', 'ward', 'an', 'nesia', 'land', 'eme', 'iant', 'wise', 'like', 'eous', 'dom', 'ify', 'eer', 'isation', 'ibly', 't', 'ible', 'ern', 'ulent', 'ization', 'ence', 'ac', 'en', 'iferious', 'ad', 'icious', 'ee', 'ary', 'sion', 'some', 'al', 'itive', 'etic', 'ive', 'ous', 'ar', 'ard', 'il', 'ocracy', 'atory', 'ship', 'ing', 'ency', 'er', 'athlon', 'gon', 'ess', 'ize', 'ation', 'able', 'id', 'ese', 'shire', 'ate', 'ics', 'ology', 'fare', 'onomy', 'ative', 'ory', 'fy', 'ologist', 'oid', 'ness', 'ography', 'ster', 'most', 'illion', 'fic', 'agogy', 'ery', 'iable', 'arch', 'ful', 'man', 'tion', 'ile', 'itude', 'uary', 'ion', 'age', 'ious', 'ance', 'esque', 'ist', 'metry', 'ancy', 'ish', 'archy', 'ism', 'y', 'or', 'ise', 'mony']
    suffixed = [word+i for i in suffixes]
    splits = [(word[:i],word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a,b in splits if b and a]
    transposes = [a + b[1] + b[0] + b[2:] for a,b in splits if len(b)>1]
    replaces = [a + c + b[1:] for a,b in splits for c in alphabet if b]
    inserts = [a + c + b for a,b in splits for c in alphabet]
    return list(set(deletes + transposes + replaces + inserts + suffixed))

class wordspellcheck(webapp.RequestHandler):
    def post(self):
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

        word = self.request.get('word')
        before = self.request.get('before')
        after = self.request.get('after')
        alternat = alternate(before,word,after)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(alternat)

        
def getjp(before,wordlist,after):               
    global REQUESTURL
    string = ''
    for x in wordlist:
        string += before+" "+x+" "+after+"\n"
    string = string.strip()
    jps = urllib2.urlopen(
        urllib2.Request(REQUESTURL,str(string))).read().split()
    for i in range(len(jps)):
        jps[i] = (float(jps[i]))#+abprobability(wordlist[i]))
    dictionary = dict(zip(wordlist,jps))
    return sorted(dictionary.iteritems(), key = lambda entity:entity[1], reverse = True)
         
        
def alternate(before,word,after):
    generated = generatefromdiff(before,word,after)
    if generated: return generated[0]
    return fromjpiter(before,word,after,0)[0]

def generatefromdiff(before,word,after):
    global GENURL
    if len(before)>0:
        generate = []
        url = GENURL+"&%s" %urllib.urlencode({'p':before})
        pat = re.compile("\w+;")
        generate = pat.findall(urllib2.urlopen(urllib2.Request(url)).read())
        for i in range(len(generate)): generate[i] = str(generate[i].strip(';'))
        match = difflib.get_close_matches(word,generate,n=1)
        if match: return(match[0],0)        
        
def fromjp(before,wordi,after,count):  # before and after are strings
    if len(before) == 0 and len(after) == 0 and len(wordi)<5: return(wordi,0)
    count += 1
    results = getjp(before,edits(str(wordi)),after) # you may edit the probabilities using language model
    dictionaryi = dict()
    dictionaryi = dict(results)
    wordjp = dictionaryi[str(wordi)]
    index = results.index((wordi,wordjp))
    if index == 0:
        return (results[0][0],0)
    elif count == 3 :
        return (results[0][0],1)
    else:
        return fromjp(before,results[0][0],after,count)
        
def fromjpiter(before,wordi,after,temp):  # temp is iseless varibla
    if len(wordi)<5:
        loop = 3
    else: loop = 5
    finaldic = dict()
    if len(wordi) < 4 and len(before) == 0 and len(after) == 0:
        return (wordi,0)
    while loop>0:
        results = getjp(before,edits(wordi),after)
        finaldic.update(dict(results[:5]))
        if results[0][0] == wordi: results[1][0]
        else: wordi = results[0][0]
        del results
        loop -= 1
    finallist = sorted(finaldic.iteritems(), key = lambda entity:entity[1], reverse = True)
    return (finallist[0][0],0)
    
def abprobability(word):   #returns the probability of the letters to be in that particular way
    prob = 0
    count = 0
    for i in range(len(word)-1):
        if word[i:i+2] not in letterprobs.prioriprob.keys(): continue
        prob += letterprobs.prioriprob[word[i:i+2]]
        count += 1
    try: asdf = round(prob/count,5)
    except: asdf = 0
    return asdf


class wordtest(webapp.RequestHandler):
    def get(self):
        variables = list()
        path = os.path.join(os.path.dirname(__file__),'wordtest.html')
        self.response.out.write(template.render(path,variables))



app = webapp.WSGIApplication([
    ('/wordspellcheck',wordspellcheck),
    #('/wordspellchec',fromjpc),
    ('/wordtest',wordtest)],
                              debug = True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()



############################ extra notes ############################

# improve the getfrom jp definition to incorpoorate abprobability function,
# and apply this only if the obtained joint probabilities are about the same, i.e .
# finalize a word if the jp difference is more than 3, and add, or may be just add
# ab probability to the resultant and apply this on the resultant

# utilise set methods to filter already obtained jp words (a = set(editwords))
# a.difference_update(b) eliminates the words from b in a












