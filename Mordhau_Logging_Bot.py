import os
import discord
import asyncio

import re
import json
import hashlib
from time import sleep
import dateutil.parser
import config
import requests
import utilMonthly as util
import time
import datetime
import traceback

playerhistoryData = {}

configServersRaw = []
for x in config.config['SERVERS']:
	configServersRaw.append(str(x)+"="+str(config.config['SERVERS'][x]))
servers = {x[0].strip(): x[1].strip() for x in [y.split("=") for y in configServersRaw]}

def readLogfilesLoop():
	
	lastDateRead = {}
	
	while True:
		for server in servers:
			logfile = open(servers[server], "r")
			for logfile_line in logfile.readlines():
				#print(logfile_line)
				if not server in lastDateRead:
					lastDateRead[server] = datetime.datetime.now()
				if 'Banned Steam ID' in logfile_line:
					lineDate = logfile_line.strip().split("]")[0].replace("[","").split(":")[0]
					#print("Date found:"+str(lineDate))
					date_object = datetime.datetime.strptime(lineDate, '%Y.%m.%d-%H.%M.%S')
					if date_object > lastDateRead[server]:
						lastDateRead[server] = date_object
						print("Going to handle message "+str(logfile_line))
						event = {}
						event['Message'] = logfile_line
						event['Server'] = server
						banhandler(event)
								
				#lastDateRead[server] = datetime.datetime.now()
			logfile.close()	
	time.sleep(5)

def banhandler(event):
	ban_message = event['Message']
	print("Parsing message {}".format(ban_message))
	steamid, ban_duration, reason = parse_message(ban_message)
	
	if steamid == "ERROR" and ban_duration == "ERROR" and reason == "ERROR":
		return None
	
	if ban_duration == 0:
		ban_duration = 'PERMANENT'
	else:
		ban_duration = int(ban_duration)
	if reason == 'Idle':
		print('Player kicked for being idle. No action required.')
		return None
	# Looking up Player name by SteamID
	print('Looking up playername by steam ID')
	steam_key = str(config.config['SETTINGS']['steam_key'].strip())
	try:
		resp = requests.get('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}'.format(steam_key, steamid))
	except:
		print ("Error looking up user on steam")
	try:
		print(resp.text)
		playername = resp.json()['response']['players'][0]['personaname']
		playeravatarlink = resp.json()['response']['players'][0]['avatarfull']
	except:
		playername = ""
		playeravatarlink = ""
		
	server = event['Server']

	playerhistory = get_playerhistory(server,steamid)
	if not playerhistory:
		playerhistory = []
	
	if not 'Vote kick' in reason:
		payload={
			'SteamId': steamid,
			'Server': server,
			'Playername': playername,
			'BanDuration': ban_duration,
			'Reason': reason,
			'PlayerAvatar': playeravatarlink,
			'BanHistory': playerhistory
		}
		handlerDiscord(payload)
	
	else:
		print('Player was kicked by vote - not sending discord notification.')
	
	playerhistory.append({
				'BanDate': datetime.datetime.isoformat(datetime.datetime.now()),
				'BanDuration': ban_duration,
				'BanReason': reason
			})

	update_playerhistory(server,steamid,playername,playerhistory)

def parse_message(message):
	if 'reason: Idle' in message:
		# Not a ban
		return None, 0, 'Idle'
	regex_capture = re.compile("Banned Steam ID (\d+), duration: (\d+), reason:(.*)?")
	regex_parse = re.search(regex_capture, message)
	if not regex_parse:
		print('Failed to parse the regex for message!!!')
		return "ERROR","ERROR","ERROR"
	steamid = regex_parse[1]
	duration = regex_parse[2]
	try:
		reason = regex_parse[3]
	except IndexError:
		reason = 'None given'
	return steamid, duration, reason

def get_playerhistory(server,steamid):
	global playerhistoryData
	
	now = datetime.datetime.now()
	year = now.year
	month = now.month
	
	try:
		playerhistoryData = util.load_data(year,month,"playerhistory")
	except:
		#traceback.print_exc()
		print("Some kind of load error")
		playerhistoryData = {}
	
	#print(playerhistoryData)
	
	if str(server) in playerhistoryData:
		#print("Server has old data")
		if str(steamid) in playerhistoryData[str(server)]:
			print("Returning old history")
			return playerhistoryData[str(server)][str(steamid)]["history"]
	
	#print("No old data found")
	return None

def update_playerhistory(server,steamid,playername,history):
	global playerhistoryData
	
	now = datetime.datetime.now()
	year = now.year
	month = now.month
	
	if not str(server) in playerhistoryData:
		playerhistoryData[str(server)] = {}
	if not str(steamid) in playerhistoryData[str(server)]:
		playerhistoryData[str(server)][str(steamid)] = {}
		playerhistoryData[str(server)][str(steamid)]["history"] = []
		playerhistoryData[str(server)][str(steamid)]["playername"] = ""
		
	playerhistoryData[str(server)][str(steamid)]["history"] = history
	playerhistoryData[str(server)][str(steamid)]["playername"] = playername
	
	#print("Going to save: "+str(playerhistoryData))
	
	util.save_data(year,month,playerhistoryData, "playerhistory")

def handlerDiscord(data):
	token = str(config.discordtoken)
	channel_id = str(config.config['SETTINGS']['channel_id'].strip())
	print('Initializing discord client.')
	client = DiscordClient(data, channel_id)
	print('Client initialized - running client.')
	run_client(client, token)

def run_client(client, *args):
	loop = asyncio.get_event_loop()
	finished = False
	while not finished:
		loop.run_until_complete(client.start(*args))
		finished = True
		print("Clearing loop")
		client.clear()


class DiscordClient(discord.Client):
	def __init__(self, ban_message, channel_id):
		super(DiscordClient, self).__init__()
		self.ban_message = ban_message
		self.channel_id = int(channel_id)
		
	async def on_ready(self):
		print('Logged on as {0}!'.format(self.user))
		print('Getting channel ID.')
		channel = self.get_channel(int(self.channel_id))
		if channel is None:
			print("ERROR: Unable to get discord channel")
			await self.close()
			
		if not self.ban_message['BanHistory']:
			past_offenses = 'NONE'
		else:
			past_offenses = '\n**------------------**\n' + '\n------------------\n'.join([
				(
					'Date: ' + m['BanDate'] +
					'\nOffense: ' + m['BanReason'] +
					'\nDuration: ' + str(m['BanDuration']) + ' (in minutes)'
				)
				for m in self.ban_message['BanHistory']
			]) + '\n**------------------**'
		print('Sending message: ', self.ban_message, 'to channel:', self.channel_id)
		message = f'''**BAN REPORT**:
	**Server**: {self.ban_message['Server']}
	**SteamId**: {self.ban_message['SteamId']}
	**Playername**: {self.ban_message['Playername']}
	**Offense**: {self.ban_message['Reason']}
	**Duration**: {self.ban_message['BanDuration']} (in minutes)

**MUGSHOT**
{self.ban_message['PlayerAvatar']}

**Previous and Current Offenses**: {past_offenses}
		'''
		
		embed = discord.Embed(description=message)
		
		await channel.send(embed=embed)
		print('Message sent, closing client.')
		await self.close()

readLogfilesLoop()