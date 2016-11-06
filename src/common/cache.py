#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	14 July 2016
# Modified 		: 	14 July 2016
# Version 		: 	1.0

"""
This script used to operate on redis-cluster
"""

import rediscluster

def get_conn(nodes):
	"""
	get a connection to the redis cluster
	parameter 'nodes' is like [{'host':'xxx','port':yyy},{'host':'xx','port':yy}]
	"""
	return rediscluster.RedisCluster(startup_nodes=nodes)


def set(conn,key,value,expire_sec):
	"""
	push a <key,value> to redis cluster

	parameter 'key' is a string
	parameter 'value' is a string or a integer
	parameter 'expire_sec' is how many seconds it will be loss
	"""
	conn.setex(key,value,expire_sec)
