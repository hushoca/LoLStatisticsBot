import xmpp
import requests
import time
from threading import Thread

apikey = "YOUR API KEY GOES HERE"
apikey2 = "YOUR SECOND API KEY GOES HERE (OR JUST DO apikey2=apikey)"
bot_username = "YOUR ACCOUNT NAME GOES HERE"
bot_password = "YOUR ACCOUNT PASSWORD GOES HERE"

platformID = "TR1"
region = "tr"

responseQueue = {};

players = {}
playerIDs = []
info = {}

def getJS(url):
	sock = requests.get(url)
	if sock.status_code != 200:
		print "STATUS CODE IS NOT 200 [STATUS CODE" + str(sock.status_code) + "]"
		return None
	js = sock.json()
	sock.close()
	return js

def getID(username):
	global apikey
	global region
	username = username.lower()
	url = "https://" + region + ".api.pvp.net/api/lol/" + region + "/v1.4/summoner/by-name/" + username + "?api_key=" + apikey
	js = getJS(url)
	if js:
		print str(js[username]['id']) ## debug
		return str(js[username]['id'])

def getChampionName(id): #no need to try except
	global apikey
	
	url = "https://global.api.pvp.net/api/lol/static-data/na/v1.2/champion/" + str(id) + "?api_key=" + apikey
	js = getJS(url)
	if js:
		print js['name'] ## debug
		return js['name']

def getPlayers(id):
	url = "https://"+region+".api.pvp.net/observer-mode/rest/consumer/getSpectatorGameInfo/"+platformID+"/"+id+"?api_key="+apikey
	js = getJS(url)
	if js:
		for pl in js['participants']:
			players[str(pl['summonerId'])] = getChampionName(pl['championId'])
			playerIDs.append(str(pl['summonerId']))

		
def getFullData():
	global apikey
	global region
	global platformID
	global playerIDs
	combinedIDs = ','.join(playerIDs)
	url = "https://"+region+".api.pvp.net/api/lol/"+region+"/v2.5/league/by-summoner/"+combinedIDs+"/entry?api_key=" + apikey2
	js = getJS(url)
	if js:
		for i in range(0, len(js)):
			buff = ""
			if playerIDs[i] in js: ##testing
				for rank in js[playerIDs[i]]:
					buff += "\t" + rank["queue"] + " = " + rank["tier"] + " " + rank["entries"][0]["division"] + " [" + str(rank["entries"][0]["leaguePoints"]) + " lp]\n"
				info[playerIDs[i]] = buff;
	else:
		print "NOT 200!"
	
connection = xmpp.Client("pvp.net")

if not connection.connect(server=("chat." + region + ".lol.riotgames.com", 5223)):
	print "COULD NOT CONNECT!"
	exit()
	
if not connection.auth(bot_username, "AIR_" + bot_password, "xiff"):
	print "COULD NOT LOGIN!"
	exit()
	
def reply(incomingm, outgoingm):
	reply = incomingm.buildReply(outgoingm)
	reply.setType("chat")
	connection.send(reply)
	
def queueClear():
	global responseQueue
	global players
	global playerIDs
	global info
	while 1:
		for user in responseQueue.keys():
			info.clear()
			players.clear()
			playerIDs = []
			
			id = getID(str(user))
			print str(user);
			getPlayers(id)
			print players
			getFullData()
			print players
			print info
			
			if any(players):
				for key in info.keys():
					buff = ""
					buff += players[key] + " :\n"
					buff += info[key]
					buff += "\n"
					print buff
					time.sleep(1)
					connection.send(xmpp.protocol.Message(responseQueue[user]['from'], buff, typ='chat'))
			else:
				connection.send(xmpp.protocol.Message(responseQueue[user]['from'], "You are not in a game", typ='chat'))
			time.sleep(2)
			responseQueue.pop(str(user),0)
		time.sleep(2);

def handler(con, msg):
	global responseQueue
	user = roster.getName(str(msg.getFrom()))
	message = msg.getBody();
	
	if message.lower() == "stats":
		responseQueue[str(user)] = msg;
		print responseQueue
	elif message.lower() == "about":
		reply(msg,"Created by Huseyin Hoca")
	else:
		reply(msg, "Type 'stats' to get the tier info.\nType 'about' to get more info.")
		
	print "\n--------------------------------------------------------------"
	print "[" + user + "] " + message
	print "--------------------------------------------------------------"
		
connection.RegisterHandler("message", handler)
connection.sendInitPresence(requestRoster=1)
roster = connection.getRoster()	

t = Thread(target=queueClear)
t.start()

while 1:
   connection.Process(1)