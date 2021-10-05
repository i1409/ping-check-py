#!/usr/bin/env python3
import os
import time
from pythonping import ping
from dotenv import load_dotenv
import mysql.connector
from telegram.ext import Updater, CommandHandler
import requests
import schedule

load_dotenv()

HOST=os.getenv('DB_HOST')
PORT=os.getenv('DB_PORT')
USER=os.getenv('DB_USER')
PASS=os.getenv('DB_PASSWORD')
DB=os.getenv('DB_NAME')
TOKEN=os.getenv('TOKEN')
CHAT=os.getenv('CHAT')

mydb = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASS,
            database=DB,
            port=PORT
        )

def getHosts():
	sql='SELECT host FROM hosts;'
	db_conn=mydb.cursor()
	try:
		db_conn.execute(sql)
		result=db_conn.fetchall()
		return result
	except Exception as err:
		print(err)
		return None

def registerPing(data: tuple):
	sql='INSERT INTO pings(host,ip,size,time_ms) VALUES(%s,%s,%s,%s)'
	db_conn=mydb.cursor()
	try:
		db_conn.execute(sql,data)
		mydb.commit()
	except Exception as err:
		print(err)
		pass
	db_conn.close()


def getLastIP(host):
	sql='SELECT ip FROM pings WHERE host=%s ORDER BY last_seen DESC LIMIT 1;'
	db_conn=mydb.cursor()
	data=(host,)
	try:
		db_conn.execute(sql,data)
		result=db_conn.fetchone()
		db_conn.close()
		return result
	except Exception as err:
		print(err)
		db_conn.close()
		return None

def registerDown(data: tuple):
	sql='INSERT INTO downs(host,ip) VALUES(%s,%s)'
	db_conn=mydb.cursor()
	try:
		db_conn.execute(sql,data)
		mydb.commit()
		db_conn.close()
	except Exception as err:
		print(err)
		db_conn.close()
		pass


def sendNotification(status, host):
	t = time.localtime()
	current_time = time.strftime("%Y-%m-%d %H:%M:%S", t)
	text="""{} - {} is now {}
Automated Notification
	""".format(current_time,host,status)
	url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
	req=requests.post(url,data ={'chat_id': CHAT, 'text': text})


def ping_check():
	for host in host_list:
		try:
			response=ping(host[0], timeout=5,count=1,size=56)
			data=list(response)
			for reply in data:
				res=str(reply).split(' ')
				if res[0] == "Reply":
					ip=res[2].split(',')[0]
					size=res[3]
					time_ms=res[6].split('ms')[0]
					data=(host[0],ip,int(size),float(time_ms))
					registerPing(data)
					for addr in host_status:
						if addr['host'] == host[0]:
							if addr['status'] != 'UP':
								addr['status']='UP'
								print("{} is now {}".format(addr['host'],addr['status']))
								sendNotification(addr['status'],addr['host'])
				else:
					ip=getLastIP(host[0])
					last_ip=ip[0]
					data=(host[0],last_ip)
					registerDown(data)
					for addr in host_status:
						if addr['host'] == host[0]:
							if addr['status'] != 'DOWN':
								addr['status']='DOWN'
								print("{} is now {}".format(addr['host'],addr['status']))
								sendNotification(addr['status'],addr['host'])
		except Exception as err:
			print(err)
			pass

def print_help(update,context):
    help_text="""This is the HELP reference guidance
send a command is as easy as type /instruction commands available:
/help   displays this HELP text
/status host  It shows the host status(UP|DOWN)
/hosts  displays all the hosts registered
    """
    context.bot.send_message(update.message.chat_id,help_text)

def print_status(update,context):
	in_hosts=update["message"]["text"].split(" ")
	in_hosts.remove('/status')
	for in_host in in_hosts:

		notfound=True
		for addr in host_status:
			if addr['host'] == in_host:
				print("{} is {}".format(addr['host'],addr['status']))
				notfound=False
				sendNotification(addr['status'],addr['host'])
		if notfound:
			text="Host {} not found in registers, Contact the Administrator".format(in_host)
			context.bot.send_message(update.message.chat_id,text)

def print_hosts(update,context):
	text=""
	for host in host_list:
		text=text+str(host[0])+"\n"
	context.bot.send_message(update.message.chat_id,text)

def print_hosts_status(update,context):
	text=""
	for host in host_status:
		text=text+host['host']+" - "+host['status']+"\n"
	context.bot.send_message(update.message.chat_id,text)
try:
	host_list=getHosts()
	host_status=[]
	for host in host_list:
		host_status.append({
			'host': host[0],
			'status': 'DOWN'
			})
	print("Getting Host from database")
except Exception as err:
	print(err)

schedule.every(1).minutes.do(ping_check)
updater=Updater(TOKEN, use_context=True)
dp=updater.dispatcher
dp.add_handler(CommandHandler('status', print_status))
dp.add_handler(CommandHandler('help', print_help))
dp.add_handler(CommandHandler('hosts', print_hosts))
dp.add_handler(CommandHandler('hosts_status', print_hosts_status))

updater.start_polling()

while True:
    schedule.run_pending()
    time.sleep(1)
updater.idle()
