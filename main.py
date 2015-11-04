import web, re, urllib
from web import form
from twilio.rest import TwilioRestClient

urls=(
	'/', 'Index',
	'/demo', 'Demo',
	'/receivesms', 'ReceiveSMS'
)

render=web.template.render('templates/')

web.config.debug=False

registerForm=form.Form(
	form.Textbox('name', description='', id='', class_='', placeholder='Full name', pattern='^.+ .+$', oninvalid='setCustomValidity("Invalid name")', onchange='try{setCustomValidity(\'\')}catch(e){}'),
	form.Password('number', description='', id='', class_='', placeholder='Phone number', pattern='^\d+$', oninvalid='setCustomValidity("Invalid phone number")', onchange='try{setCustomValidity(\'\')}catch(e){}'),
	form.Password('code', description='', id='', class_='', placeholder='Security code', pattern='^.+$'),
	form.Button('Submit', class_='centertext')
)

db=web.database(dbn='mysql', db='', user='', pw='')

account_sid = ""
auth_token  = ""
client = TwilioRestClient(account_sid, auth_token)

class Index:
	def GET(self):
		return render.index()

class Demo:
	def GET(self):
		statuses=db.query('SELECT * FROM statuses')
		return render.demo(registerForm, statuses)
	def POST(self):
		form=registerForm
		if not form.validates():
			raise web.seeother('/#formdidnotvalidate')
		name=form.d.name
		number=form.d.number
		code=form.d.code

		###### security checks ######
		if not number.isdigit():
			raise web.seeother('/#numberdidnotvalidate')
		if not code=="cats":
			raise web.seeother('/#invalidsecuritycode')

		try:
			message = client.messages.create(body="Thanks for registering with us!",
				to="+" + str(number),
				from_="+")
		except Exception as e:
			raise web.seeother('/#invalidnumber')

		db.insert('users', name=name, phone=number)
		db.insert('statuses', phone=number, status="I just joined Future SMS!", name=name)
		raise web.seeother('/demo')

class ReceiveSMS:
	def GET(self):
		return "You shouldn't be here, this is POST-only!"
	def POST(self):
		fromNum=re.findall('(?<=From=%2B1)(.*)(?=&ApiVersion=)', web.data())[0]

		try:
			name=db.query('SELECT name FROM users WHERE phone=' + fromNum)[0]['name']
		except IndexError:
			message = client.messages.create(body="You aren't registered! Do so at <todo:put site url here>.",
				to="+" + str(fromNum),
				from_="+")
			return False

		msg=re.findall('(?<=&Body=)(.*)(?=&FromCountry)', web.data())[0]
		msg=msg.replace('+', '%20')
		msg=urllib.unquote(msg)

		db.update('statuses', where='phone=' + fromNum, status=msg)

		message = client.messages.create(body="Alright " + name + ", I've set your status to \"" + str(msg) + "\"",
				to="+" + str(fromNum),
				from_="+")



if __name__=="__main__":
	app=web.application(urls, globals())
	app.run()