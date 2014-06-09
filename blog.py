import webapp2
import  jinja2
from google.appengine.ext import db
import os
import urllib2
from xml.dom import minidom
import json



#get key for the particular entity
def blog_key(name='default'):
	return db.Key.from_path('blogs',name)

#get path of templates' directory
template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
	autoescape=True)




class Post(db.Model): 
	"""Database Model for Posts"""
	subject=db.StringProperty(required=True)
	content=db.TextProperty(required=True)
	content_ex=db.TextProperty()
	created=db.DateTimeProperty(auto_now_add=True)
	modified=db.DateTimeProperty(auto_now=True)

	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)

                 
	def render_front(self):
		#renders first page
		if self.content_ex:
			self._render_text=self.content_ex.replace('\n','<br>')
		return self.render_str("post.html",p=self)
                 
	def render(self):
		#renders page for particular post
		self._render_text=self.content.replace('\n','<br>')
		if self.content_ex:
			self._render_text1=self.content_ex.replace('\n','<br>')
		return self.render_str("post1.html",p=self)

	def as_dict(self):
		"""to convert items requested by json to a dictionary""" 
		time_fmt='%c'
		d={'subject':self.subject,
		        'content':self.content,
		        'created':self.created.strftime(time_fmt),
		        'content_ex':self.content_ex,
		        'last_modified':self.modified.strftime(time_fmt)}
		return d



class BlogHandler(webapp2.RequestHandler):
	"""To avoid calling self.response.write repeatedly"""
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)

	def render_str(self,template,**params):
		"""pass parameters to template and render it"""
		t=jinja_env.get_template(template)
		return t.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

	def render_json(self,d):
		"""json rendering if url ends with .json"""
		json_txt=json.dumps(d)
		self.response.headers['Content-Type']='application/json;charset=UTF-8'
		self.write(json_txt)

	def initialize(self,*a,**kw):
		webapp2.RequestHandler.initialize(self,*a,**kw)
		if self.request.url.endswith('.json'):
			self.format='json'
		else:
			self.format='html'

class BlogFront(BlogHandler):
	#Handler for front page
	def get(self):
		"""Get all the  post from database and display them 
		according to their creation time """
       		posts=greetings=Post.all().order('-created')
       		if self.format=='html':
			self.render('front.html',posts=posts)
		else:
			"""renders json o/p according to prescribed format for front page"""
			return self.render_json([p.as_dict() for p in posts])

class PostPage(BlogHandler):
	def get(self,post_id):
		key=db.Key.from_path('Post',int(post_id),parent=blog_key())
		post=db.get(key)

		if not post:
			self.error(404)
			return
		if self.format=='html':
			self.render("permalink.html",post=post)
		else:
			"""renders json o/p in prescribed format for post"""
			self.render_json(post.as_dict())


class newPost(BlogHandler):
	"""To add new post to the blog"""
	def get(self):
		self.render("newpost.html")

	def post(self):
		subject=self.request.get('subject')
		content=self.request.get('content')
		content_ex=self.request.get('content_ex')

		if subject and content:
			p=Post(parent=blog_key(),subject=subject,content=content,content_ex=content_ex)
			p.put()
			self.redirect('/blog/%s'%str(p.key().id()))
		else:
			error="subject and content,please!"
			self.render("newpost.html",subject=subject,content=content,error=error)

class Resume(BlogHandler):
	#Handler for front page
	def get(self):
		self.render("resume.html")



"""URL handlers for particular URL"""
application = webapp2.WSGIApplication([
     ('/', BlogFront),
     ('/.json',BlogFront),
    ('/blog/?(?:\.json)?', BlogFront),
    ('/blog/newpost',newPost),
    ('/blog/([0-9]+)(?:\.json)?',PostPage),
    ('/blog/resume',Resume),
], debug=True)