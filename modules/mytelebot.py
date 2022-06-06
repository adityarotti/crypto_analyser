import time,os
import pickle
import collections
import telegram
import glob
import numpy as np

path_to_this_file=os.path.dirname(os.path.abspath(__file__))

class open_subscribers_log_book(object):
	def __init__(self):
		self.filename=path_to_this_file + "/../userdata/subscriber_list"
		if not(os.path.isfile(self.filename)):
			userfile = open(self.filename, "wb")
			pickle.dump({}, userfile)
			userfile.close()
		self.subscriber_dict=pickle.loads(open(self.filename, 'rb').read())

	def close_user_list(self,):
		userfile = open(self.filename, "wb")
		pickle.dump(self.subscriber_dict, userfile)
		userfile.close()
	
	def add_subscriber(self,x):
		if x.message.chat_id not in self.subscriber_dict.keys():
			self.subscriber_dict[x.message.chat_id]={}
			self.subscriber_dict[x.message.chat_id]["first_name"]=x.message.chat.first_name
			self.subscriber_dict[x.message.chat_id]["last_name"]=x.message.chat.last_name
			self.subscriber_dict[x.message.chat_id]["date added"]=time.ctime()
			self.subscriber_dict[x.message.chat_id]["coin pair"]=["BTCUSD"]
			return "done"
		else:
			return None

	def remove_subscriber(self,x):
		if x.message.chat_id in self.subscriber_dict.keys():
			del self.subscriber_dict[x.message.chat_id]
			return "done"
		else:
			return None

	def add_coinpair_to_user_portfolio(self,x):
		coinpair=x.message.text
		coinpair=coinpair.replace(" ","")
		coinpair=coinpair.split(":")[1].upper()
		if coinpair not in self.subscriber_dict[x.message.chat_id]["coin pair"]:
			self.subscriber_dict[x.message.chat_id]["coin pair"]=self.subscriber_dict[x.message.chat_id]["coin pair"] + [coinpair]

		status="["
		for coins in self.subscriber_dict[x.message.chat_id]["coin pair"]:
			status=status + coins + ","
		status=status[:len(status)-1] + "]"
		return status

class init_mybot(object):
	def __init__(self,test=True):
		self.test=test
		mybot_token='XYZ'
		self.bot=telegram.Bot(token=mybot_token)
		self.bot_sbs=open_subscribers_log_book()
		self.bot_init_file=path_to_this_file + "/../userdata/bot_init.txt"
		self.update_id_file=path_to_this_file + "/../userdata/update_id.txt"
		self.manager_id_file=path_to_this_file + "/../userdata/manager_id.txt"
		self.manager_id=[int(np.loadtxt(self.manager_id_file))]
		self.get_bot_updates()
		self.send_welcome_msg()
		
	def get_bot_updates(self,):
		if os.path.isfile(self.update_id_file):
			self.update_id=int(np.loadtxt(self.update_id_file))
			self.bot_updates=self.bot.getUpdates(offset=self.update_id+1)
		else:
			self.bot_updates=self.bot.getUpdates()
	
		if len(self.bot_updates)>0:
			self.update_id=self.bot_updates[-1].update_id
			with open(self.update_id_file, 'w') as f:
				f.write('%d' % self.update_id)

	def update_subscriber_preferences(self,):
		for i in range(len(self.bot_updates)):
			if self.bot_updates[i].message!=None:
				if self.bot_updates[i].message.chat_id not in self.manager_id:
					usrmsg=self.bot_updates[i].message.chat.first_name + " "
					usrmsg=usrmsg + self.bot_updates[i].message.chat.last_name + " says: "
					usrmsg=usrmsg + self.bot_updates[i].message.text
					for man_id in self.manager_id:
						self.bot.send_message(chat_id=man_id,text=usrmsg)
				if "/EXIT" in self.bot_updates[i].message.text.upper():
					status=self.bot_sbs.remove_subscriber(self.bot_updates[i])
					if status =="done":
						self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text="Removed from subscriber list")
				if "/START" in self.bot_updates[i].message.text.upper():
					status=self.bot_sbs.add_subscriber(self.bot_updates[i])
					if status =="done":
						self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text="Added to subscriber list")
						self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text=wel_msg)
						self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text=init_msg)
						self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text=instr_msg)
				if "/INSTR" in self.bot_updates[i].message.text.upper():
					self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text=instr_msg)
				if "/ADDCOIN" in self.bot_updates[i].message.text.upper():
					status=self.bot_sbs.add_coinpair_to_user_portfolio(self.bot_updates[i])
					self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text="Your coin portfolio: " + status)
				if "/MYCOINS" in self.bot_updates[i].message.text.upper():
					status="["
					for coins in self.bot_sbs.subscriber_dict[self.bot_updates[i].message.chat_id]["coin pair"]:
						status=status + coins + ","
					status=status[:len(status)-1] + "]"
					self.bot.send_message(chat_id=self.bot_updates[i].message.chat.id,text="Your coin portfolio: " + status)
			self.bot_sbs.close_user_list()
	
	def broadcast_cryptoupdate(self,):
		list_of_files = glob.glob(path_to_this_file + "/../outdata/*")
		list_of_files = [f for f in list_of_files if "gif" not in f]
		#list_of_files = glob.glob(path_to_this_file + "/../outdata/gif/*")
		latest_file = max(list_of_files, key=os.path.getctime)
		if self.test:
			user_id_list=[x for x in self.bot_sbs.subscriber_dict.keys() if x in [1709448407,449208196]]
		else:
			user_id_list=self.bot_sbs.subscriber_dict.keys()
		print(latestfile)
		crypstatpng=open(latest_file,"rb")
		for chid in user_id_list:
			# This will only fail if the user has unsubscribed from the bot.
			# So remove the chid from the subscriber database.
			try:
				self.bot.send_photo(chat_id=chid,photo=crypstatimg)
				#self.bot.send_animation(chat_id=chid,animation=open(latest_file,"rb"))
			except:
				usrmsg=self.bot_sbs.subscriber_dict[chid]["first_name"] + " "
				usrmsg=usrmsg + self.bot_sbs.subscriber_dict[chid]["last_name"]
				usrmsg=usrmsg + " stopped the bot"
				for man_id in self.manager_id:
					self.bot.send_message(chat_id=man_id,text=usrmsg)

				del self.bot_sbs.subscriber_dict[chid]
				self.bot_sbs.close_user_list()

	def send_welcome_msg(self,):
		'''
		Send this when starting the bot for the first time for all subscribers.
		'''
		self.bot_init_status=int(np.loadtxt(self.bot_init_file))
		if self.bot_init_status==0:
			if self.test:
				user_id_list=[x for x in self.bot_sbs.subscriber_dict.keys() if x in [1709448407,449208196]]
			else:
				user_id_list=self.bot_sbs.subscriber_dict.keys()

			for chid in user_id_list:
				try:
					self.bot.send_message(chat_id=chid,text=wel_msg)
					self.bot.send_message(chat_id=chid,text=init_msg)
					self.bot.send_message(chat_id=chid,text=instr_msg)
				except:
					None

			self.bot_init_status=1
			with open(self.bot_init_file, 'w') as f:
				f.write('%d' % self.bot_init_status)

# Welcome message
wel_msg = "Hello! Crypto enthusiast! \n"
wel_msg = wel_msg + "This telegram bot periodically provides charts \n"
wel_msg = wel_msg + "composed of statistical indicators to help make trading calls \n \n"

#Initialisation message
init_msg = " The bot is coming to life !!!\n"
init_msg = init_msg + "This bot will be running on my laptop"
init_msg = init_msg + " so expect downtimes. But hopefully I can keep it running pretty regularly."
init_msg = init_msg + " Hope you find the inputs from this bot useful. Please provide feedback and I am eager to hear from you if you have ideas to improve it (inclusion of other statistical indicators)."
init_msg = init_msg + " The idea is to grow it into a reliable trading tool with enhanced usefullness as we ourselves learn and evolve from our trading experiences."
init_msg = init_msg + " \n \n"

init_msg = init_msg + "**Some technical details : ** \n"
init_msg = init_msg + "-->The buy sell signal are estimated from the MACD and RSI indicators, with current RSI threshold set at [35.,65.] \n"
init_msg = init_msg + "--> EMA7 sl and EMA15 sl are slopes that are given in units of EMA30 - a more stable, slowly varying entity owing to its long lever arms. The numbers can be interpreted as percentage changes w.r.t EMA30. General rule of thumb you want to be holding the asset when these indicators are positive and relatively large. The amplitudes could also be thought of as volatility indicators. \n \n"

#init_msg = init_msg + "**IMPORTANT :\n"
#init_msg = init_msg + "I am a novice in trading with some backgroun in analytical fields, so a lot of the current development is based on my naive understanding of trading and statistical indicators. So always bear this in mind"

# Instruction message
instr_msg = "\n----------------------------------------\n"
instr_msg = instr_msg + "/exit : to be removed from subscription \n"
instr_msg = instr_msg + "/start : to get re-subscribed \n"
instr_msg = instr_msg + "/addcoin : to add coin to subscription\n"
instr_msg = instr_msg + "e.g: /coin:BTCUSD to add BTC to your coin list \n"
instr_msg = instr_msg + "/mycoins : returns current coin subscription list \n"
instr_msg = instr_msg + "/instr : to get list of commands \n"
instr_msg = instr_msg + "\n **Upcoming features **: \n"
instr_msg = instr_msg + "--> User tailored crypto coin updates \n"
instr_msg = instr_msg + "--> Set cadence of updates \n"
instr_msg = instr_msg + "----------------------------------------\n"
