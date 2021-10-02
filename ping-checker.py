#!/usr/bin/env python3
import os
import time
from pythonping import ping


while True:
	hosts=open("hosts.txt","r")
	host_list=[]
	for line in hosts:
		host_list.append(line.split()[0])

	for host in host_list:
		response=ping(host, timeout=5,count=1,size=56)
		data=list(response)
		for reply in data:
			res=str(reply).split(' ')
			if res[0] == "Reply":
				print("{} -> {} {} bytes {}".format(host,res[2].split(',')[0],res[3],res[6]))
			else:
				print("{} -> {}".format(host,reply))
	time.sleep(60)



