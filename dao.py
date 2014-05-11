#!flask/bin/python
import json as simplejson
from flask import Flask, g, request
from couchdb.design import ViewDefinition
import flask.ext.couchdb
import couchdb
from couchdb.mapping import Document, TextField, IntegerField, DateTimeField
import datetime
from documents import *
from StringIO import StringIO
from io import BytesIO
import pycurl


app = Flask(__name__)

get_passwords = ViewDefinition('login', 'password', 
                                'function(doc) {if(doc.doc_type =="User")emit(doc.emailId, doc.password);}')


get_userId = ViewDefinition('login', 'userId',
                                'function(doc) {if(doc.doc_type =="User")emit(doc.emailId, doc.userId);}')

#to get all boards for a user
get_boards = ViewDefinition('userId', 'board', 
                                'function(doc) {if(doc.doc_type =="Board")emit(doc.userId,doc);}')

#to get board by boardname for a user
#need to change the design model and view name cant keep same as above
get_board = ViewDefinition('get', 'board', 
                                'function(doc) {if(doc.doc_type =="Board")emit([doc.userId,doc.boardName],doc);}')

get_pins = ViewDefinition('userId', 'pins', 
                                'function(doc) {if(doc.doc_type =="Pin")emit([doc.userId,doc.boardName],doc);}')

get_comments = ViewDefinition('userId', 'comments', 
                                'function(doc) {if(doc.doc_type =="Comment")emit([doc.userId,doc.boardName,doc.pinId],doc);}')

#to update a pin
update_pin = ViewDefinition('update', 'pin', 
                                'function(doc) {if(doc.doc_type =="Pin")emit([doc.userId,doc.boardName,doc.pinId],doc);}')

#to update a board
update_board = ViewDefinition('update', 'board', 
                                'function(doc) {if(doc.doc_type =="Board")emit([doc.userId,doc.boardName],doc);}')


def register(fname,lname,email,passw):
	docs = []
    	for row in get_userId(g.couch):
		docs.append(row.value)

	if not docs:	
		uid = 0
	else:
		uid = docs[-1]
	
	user = User(
		firstName = fname,
		lastName = lname,
		emailId= email, 
		password = passw,
		userId = uid+1
		)
	user.store()
	return None


def checkPass(emailId,password):
	docs = []
    	for row in get_passwords(g.couch)[emailId]:
        	docs.append(row.value)


		if password == row.value:
			return True
		else:
			return False

def createboard(uid, bName,bDesc,bcategory,bisPrivate):
	board = Board(
			userId = uid,
			boardName = bName,
			boardDesc = bDesc,
			category = bcategory,
			isPrivate = false
		     )
	
	board.store()
	return None


def createpin(uid,bName,pName,pimage,pdesc):
	docs = []
    	for row in get_pins(g.couch)[int(uid),bName]:
		docs.append(row.value)

	if not docs:	
		pid = 0
	else:
		pid = docs[-1]

	pin = Pin(
			userId = uid,
			boardName = bName,
			pinName = pName,
			image = pimage,
			description = pdesc,	
			pinId = pid+1
		     )
	
	pin.store()
	return None



def getpins(userId,bName):
	pins = []
    	for row in get_pins(g.couch)[int(userId),bName]:
		pins.append(row.value)
		
	return pins


def updatepin(uid,bName,pName,pimage,pdesc,pid):
		
	for row in update_pin(g.couch)[int(uid),bName,int(pid)]:
		pin = row.value
	
	print 'pin is',pin['pinName']	
	
 	
	if(pName is None):
   		pName = pin['pinName']
		
	if(pimage is None):
   		pimage = pin['image']
		
	if(pdesc is None):
   		pdesc = pin['description']

	newpin = Pin(
			userId = uid,
			boardName = bName,
			pinName = pName,
			image = pimage,
			description = pdesc,	
			pinId = pid
		     )
	newpin.store()
	
	for row in update_pin(g.couch)[int(uid),bName,int(pid)]:
		pin = row.value
	
    	
	return pin
	
def updateboard(uid,bDesc,bName,categ):
		
	for row in update_board(g.couch)[int(uid),bName]:
		board = row.value
	
	#print 'board is', board['boardName']	
	
 	
	if(bDesc is None):
   		bDesc = board['boardDesc']
		
	if(bName is None):
   		bName = board['boardName']
		
	if(categ is None):
   		categ = board['category']

	newboard = Board(
			userId = uid,
			boardName = bName,
			boardDesc = bDesc,	
			category = categ
		     )
	newboard.store()
	
	for row in update_board(g.couch)[int(uid),bName]:
		board = row.value
	
    	
	return board


def getBoardsForUser(userId):
	#return get_boards(g.couch)[userId]
	boards = []
	
    	for row in get_boards(g.couch)[int(userId)]:
		boards.append(row.value)

	#print 'BOARDS' ,boards
	#return simplejson.dumps(boards)

		
	return boards

def getBoardByBoardname(userId, bname):
	board = []
	print userId,bname
	for row in get_board(g.couch)[int(userId),bname]:
		board.append(row.value)

	return board


def createcomment(uid,bName,pId,cDesc):
	comments = []
    	for row in get_comments(g.couch)[int(uid),bName]:
		comments.append(row.value)

	if not comments:	
		cid = 0
	else:
		cid = comments[-1]

	comment = Comment(
			userId = uid,
			boardName = bName,
			pinId = pId,
			commentId = cid+1,
			commentDesc = cDesc
		     )
	
	comment.store()
	return None


def deleteBoardForuser(userId, bname):
	board = getBoardByBoardname(userId,bname)
	ourboard = board[0]
	print ourboard['_id']
	url = 'http://localhost:5984/pinboard/'+ ourboard['_id']+ ' -d \'{"rev":"\''+ourboard['_id']+'"}'
	url = 'http://localhost:5984/pinboard/'+ ourboard['_id']+ ' -d \'{"rev":"'+ourboard['_rev']+'"}\''
	print url
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
	c.perform()
	return None

