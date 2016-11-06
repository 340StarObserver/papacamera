#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	04 August 2016
# Modified 		: 	04 August 2016
# Version 		: 	1.0

"""
This script used to operate on mongodb
"""

import random

from pymongo import MongoClient
from bson import ObjectId


def get_conn(hosts,user,pwd,db_name):
	"""
	get a MongoClient object

	parameters :
		'hosts' is like ["host1:port1","host2:port2","host3:port3"]
			each one is a mongos node or mongod node
		'user' is the username of this database
		'pwd' is the password of this database
		'db_name' is the name of this database
	tip :
		don't forget to close the MongoClient after your use
	"""
	num=len(hosts)
	index=random.randint(0,num-1)
	conn=MongoClient(hosts[index])
	conn[db_name].authenticate(user,pwd,mechanism='SCRAM-SHA-1')
	return conn


def get_one(conn,db_name,collection_name,object_id):
	"""
	get one document from mongo

	parameters :
		'conn' is a MongoClient, you can create it by function 'get_conn'
		'db_name' is the name of your database
		'collection_name' is the name of your collection
		'object_id' is a string id
	"""
	res=conn[db_name][collection_name].find_one({"_id":ObjectId(object_id)})
	res["_id"]=object_id
	return res
