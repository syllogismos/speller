

import os
import cgi
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import speller
import urllib2

#lexicon = urllib2.urlopen(urllib2.Request("http://localhost:8082/words")).read().split()


def edits(word):
    alphabet = 'abcdedfghijklmnopqrstuvwxyz'
    splits = [(word[:i],word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a,b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a,b in splits if len(b)>1]
    replaces = [a + c + b[1:] for a,b in splits for c in alphabet if b]
    inserts = [a + c + b for a,b in splits for c in alphabet]
    return list(set(deletes + transposes + replaces + inserts))

class train(webapp.RequestHandler):
    def post(self):
        wordlist = self.request.get('word').split("\n")
        entities = list()
        for query in wordlist:
            query = query.split()
            word = query[0]
            entity = speller.lexicon0(word = word, key_name = word)
            entity.known = query[1:]
            entities.append(entity)
        db.put_async(entities).get_result()

class trainer(webapp.RequestHandler):
    def get(self):
       variables = list()
       path = os.path.join(os.path.dirname(__file__),'trainer.html')
       self.response.out.write(template.render(path,variables))


app = webapp.WSGIApplication([
    ('/train',train),
    ('/trainer',trainer)],
                      debug = True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()
