#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	13 July 2016
# Modified 		: 	12 August 2016
# Version 		: 	1.0

"""
This script used to read configuration from a file
"""

import ConfigParser
import sys


def read(filename):
	"""
	this function used to read configuration from a file

	the parameter is the path of file, recommend use the absoluate path
	it returns a dictionary of pairs of <key,value>
	"""
	conf={'webserver':{},'kafka':{},'redis':{},'hadoop':{},'consumer':{},'mongo':{},'oss':{},'resultlog':{}}
	config=ConfigParser.ConfigParser()
	try:
		config.read(filename)
		conf['webserver']['host']=config.get('webserver','host')
		conf['webserver']['port']=int(config.get('webserver','port'))
		conf['kafka']['servers']=config.get('kafka','servers').split(',')
		conf['kafka']['topic']=config.get('kafka','topic')
		conf['kafka']['key_len']=int(config.get('kafka','key_len'))
		conf['kafka']['key_seed']=config.get('kafka','key_seed')
		conf['kafka']['binpath']=config.get('kafka','binpath')
		conf['kafka']['datapath']=config.get('kafka','datapath')
		conf['kafka']['logpath']=config.get('kafka','logpath')
		conf['kafka']['confdir']=config.get('kafka','confdir')
		conf['kafka']['zookeeper']=config.get('kafka','zookeeper')
		conf['kafka']['msg_size']=int(config.get('kafka','msg_size'))
		node_list=config.get('redis','servers').split(',')
		node_num=len(node_list)
		cluster=[]
		i=0
		while i<node_num:
			node=node_list[i].split(':')
			cluster.append({'host':node[0],'port':node[1]})
			i+=1
			del node
		del node_list
		conf['redis']['servers']=cluster
		conf['redis']['db_num']=int(config.get('redis','db_num'))
		conf['redis']['retry_limit']=int(config.get('redis','retry_limit'))
		conf['redis']['retry_time']=float(config.get('redis','retry_time'))
		conf['redis']['expire']=int(config.get('redis','expire'))
		conf['hadoop']['hosts']=config.get('hadoop','hosts')
		conf['hadoop']['username']=config.get('hadoop','username')
		conf['hadoop']['hdfs_host']=config.get('hadoop','hdfs_host')
		conf['hadoop']['hdfs_port']=int(config.get('hadoop','hdfs_port'))
		conf['hadoop']['topic']=config.get('hadoop','topic')
		conf['consumer']['app_name']=config.get('consumer','app_name')
		conf['consumer']['logpath']=config.get('consumer','logpath')
		conf['mongo']['hosts']=config.get('mongo','hosts').split(',')
		conf['mongo']['dbname']=config.get('mongo','dbname')
		conf['mongo']['collection']=config.get('mongo','collection')
		conf['mongo']['user']=config.get('mongo','user')
		conf['mongo']['pwd']=config.get('mongo','pwd')
		conf['oss']['access_id']=config.get('oss','access_id')
		conf['oss']['access_key']=config.get('oss','access_key')
		conf['oss']['host']=config.get('oss','host')
		conf['oss']['bucket']=config.get('oss','bucket')
		conf['oss']['oss_dir']=config.get('oss','oss_dir')
		conf['resultlog']['hdfs_topic']=config.get('resultlog','hdfs_topic')
		conf['resultlog']['batch_size']=int(config.get('resultlog','batch_size'))
	except StandardError,e:
		print "failed to read conf, reason is %s"%(e)
		sys.exit(1)
	except:
		print "failed to read conf, may be your path is not exist"
		sys.exit(1)
	return conf


if __name__ == '__main__':
	"""
	test for this script
	"""
	data=read("../../conf/server.conf")
	print data
