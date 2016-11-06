#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	13 July 2016
# Modified 		: 	12 August 2016
# Version 		: 	1.0

"""
This script used to deal requests of distinguish a picture from client

run this script :
1. modify the conf file, which declared in line 30
2. python main.py >/mydata/program/sparkserver/webserver/2016xxxx.log 2>&1 &
"""

import random
import time
import sys
import base64

import flask
import kafka

sys.path.append("../common")
import configure
import cache

# read the global confguration
conf=configure.read("../../conf/server.conf")

# create an app
app=flask.Flask(__name__)


def rand_key(length,seed):
	"""
	get a rand and unique key

	parameter 'length' is the length of rand string
	parameter 'seed' is the seed string

	the key is combined by current timestamp and a rand string
	for example:
		current timestamp is 1445599887
		length=8
		seed='abcdefghijkmnopqrstuvwxyz'
	then : a possible key may be 1445599887acegiknp
	"""
	sa=[]
	i=0
	while i<length:
		sa.append(random.choice(seed))
		i+=1
	return "%d%s"%(int(time.time()),''.join(sa))


@app.route("/distinguish",methods=['POST'])
def distinguish():
	"""
	deal requests for distinguish a picture from client

	1. accept the image(base64) and GPS
	2. send a message to kafka
		its key is a unique rand string
		its value is the binary content of the file
	3. ask redis whether the result has been calculated
		each time the result have not been calculated, sleep some time
	"""
	global conf
	post_data=dict(flask.request.form)
	img_value=None
	user_id=0
	pos_x=200
	pos_y=200
	try:
		img_value=base64.b64decode(post_data['targetfile'][0])
		if int(post_data['has_gps'][0]) is 1:
			pos_x=float(post_data['pos_x'][0])
			pos_y=float(post_data['pos_y'][0])
		user_id=int(post_data['user_id'][0])
	except:
		pass

	size_KB=0
	if img_value is not None:
		size_KB=(len(img_value)>>10)
	ad_info=None
	if size_KB>0 and size_KB<=conf['kafka']['msg_size']:
		request_id=rand_key(conf['kafka']['key_len'],conf['kafka']['key_seed'])
		msg_key="%s,%d,%f,%f"%(request_id,user_id,pos_x,pos_y)
		producer=kafka.KafkaProducer(bootstrap_servers=conf['kafka']['servers'],key_serializer=str.encode,acks='all')
		producer.send(conf['kafka']['topic'],key=msg_key,value=img_value)
		producer.close()

		retry_limit=conf['redis']['retry_limit']
		retry_time=conf['redis']['retry_time']
		cache_conn=cache.get_conn(conf['redis']['servers'])
		i=0
		while i<retry_limit:
			ad_info=cache_conn.get(request_id)
			if ad_info is not None:
				break
			i+=1
			time.sleep(retry_time)
		del request_id
		del msg_key
	if ad_info is None:
		ad_info='{}'
	del img_value
	del post_data
	return ad_info


if __name__ == '__main__':
	app.run(host=conf['webserver']['host'],port=conf['webserver']['port'])
