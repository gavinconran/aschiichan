import os
import re
import sys
import urllib2
from xml.dom import minidom
from string import letters
from google.appengine.ext import db
import webapp2
import jinja2
import logging
from google.appengine.api import memcache
import time

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
def gmap_img(points):
        markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
        return GMAPS_URL + markers

IP_URL  = "http://api.hostip.info/?ip="
def get_coords(ip):
        url = IP_URL + ip
        content = None
        try:
                content = urllib2.urlopen(url).read()
        except urllib2.URLError:
                return
          
        if content:
                d = minidom.parseString(content)
                coords = d.getElementsByTagName("gml:coordinates")
                if coords and coords[0].childNodes[0].nodeValue:
                        lon, lat = coords[0].childNodes[0].nodeValue.split(',')
                        return db.GeoPt(lat, lon)

template_path = os.path.join(os.path.dirname(__file__))
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), autoescape =True
    )

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        

def top_arts(update = False):
        key = 'top'
        arts = memcache.get(key)
        if arts is None or update:
          logging.error("DB QUERY")
          arts = db.GqlQuery("SELECT * "
                             "FROM Art "
                             #"WHERE ANCESTOR IS :1 "
                             "ORDER BY created DESC "
                             "LIMIT 10"#,
                             #art_key
                             )
          arts = list(arts)
          memcache.set(key, arts)
        return arts  
      
class MainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = top_arts()
        # get coords
        points = filter(None, (a.coords for a in arts))
        # if we have any coords, make an image-url
        
        # display the image-url
        img_url = None
        if points:
          img_url = gmap_img(points)
        
        #self.write(repr(points))
        self.render("front.html", title=title, art=art, error = error, arts = arts, img_url = img_url)
        
    def get(self):
        self.render_front()
        
    def post(self):
    	title = self.request.get("title") 
    	art = self.request.get("art")
        if title and art:
           #ip = self.request.remote_addr
           ip = '86.135.232.240'
           #ip = "37.158.94.166" 
           #ip = "4.2.2.2"
           #ip = "23.24.209.141"
           #ip = "212.58.246.95"
           #ip = "170.149.100.10"
           #ip = "129.78.32.24"
           #ip = "133.51.69.0"
           
           a = Art(title = title, art = art)
           #lookup the user's coordinates from their IP address
           coords = get_coords(ip)
           # if we have coordinates, add them to the Art 
           if coords:
              a.coords = coords
              
           a.put()
           # rerun the query and update the cache
           top_arts(True)
           self.redirect("/")
        else:
           error = "we need both a title and some artwork!" 
           self.render_front(title=title, art=art, error = error)
            
class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()
    
    
APP = webapp2.WSGIApplication([('/', MainPage)], debug=True)




