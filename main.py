#!/usr/bin/env python
#
# Copyright 2012 teja Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.api import users

class TodoModel(db.Model):
    author = db.UserProperty(required=True)
    shortDescription = db.StringProperty(required=True)
    longDescription = db.StringProperty(multiline=True)
    url = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    dueDate = db.StringProperty(required=True)
    finished = db.BooleanProperty()

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

        active = TodoModel.gql("WHERE author = :author and finished=false",
                              author=users.get_current_user())
        done = TodoModel.gql("WHERE author = :author and finished=true",
                             author=users.get_current_user())

        values = {
            'active': active,
            'done' : done,
            'numberactive': active.count(),
            'numberdone' : done.count(),
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            }
        self.response.out.write(template.render('templates/index.html', values))

class BaseRequestHandler(webapp.RequestHandler):
    """Base request handler extends webapp.Request handler

     It defines the generate method, which renders a Django template
     in response to a web request
  """

class New(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            testurl = self.request.get('url')
            if not testurl.startswith('http://') and testurl:
                testurl = 'http://' + testurl

            todo = TodoModel(
                author=users.get_current_user(),
                shortDescription=self.request.get('shortDescription'),
                longDescription=self.request.get('longDescription'),
                dueDate=self.request.get('dueDate'),
                url=testurl,
                finished=False
            )
            todo.put()

        self.redirect('/')

class Email(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            todo = TodoModel.get_by_id(id)
            message = mail.EmailMessage(
                sender=user.email(),
                subject=todo.shortDescription
            )
            message.to = user.email()
            message.body = todo.longDescription
            message.send()

        self.redirect('/')

class Delete(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            todo = TodoModel.get_by_id(id)
            todo.delete()
        self.redirect('/')
        
class Done(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            todo = TodoModel.get_by_id(id)
            todo.finished = True
            todo.put()
        self.redirect('/')

class Undo(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            todo = TodoModel.get_by_id(id)
            todo.finished = False
            todo.put()
        self.redirect('/')

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/new', New),
        ('/delete', Delete),
        ('/email', Email),
        ('/undo', Undo),
        ('/done', Done)
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
