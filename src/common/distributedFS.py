#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	20 July 2016
# Modified 		: 	12 August 2016
# Version 		: 	1.0

"""
This script used to do something with the HDFS

1. get a connect to HDFS
2. put the feature(binary format) of an image to HDFS
3. judge whether a file exists in HDFS
4. get an image's feature(binary format) from HDFS
5. get a list of images' feature(binary format) from HDFS
6. get all images' feature(binary format) from HDFS
"""

import pyhdfs

def get_conn(hosts,user):
	"""
	get a client of hadoop distributed file system

	parameter :
		'hosts' is like 'host1:port1,host2:port2', use ',' to divide different server
		'user' is the user of hadoop
	"""
	return pyhdfs.HdfsClient(hosts=hosts,user_name=user)


def put_feature(conn,topic,img_id,feature_bin):
	"""
	put feature data of an image into HDFS

	parameter :
		'conn' is a client object, you can create it by use the above function 'get_conn'
		'topic' is the topic of your files, you can view it as a dictionary
		'img_id' is the id of a picture, it is a global unique string key
		'feature_bin' is the binary(that is to say after serialize) of an image's feature
	for example :
		topic=img_feature,img_id=abcde,
		then it will push a file into HDFS, it is hdfs://host:port/img_feature/abcde
	"""
	path="/%s/%s"%(topic,img_id)
	conn.create(path,feature_bin,overwrite=True)
	del path


def exist_feature(conn,topic,img_id):
	"""
	judge whether exist such a feature data in HDFS

	parameter :
		'conn' is a client object, you can create it by use the above function 'get_conn'
		'topic' is the topic of your files, you can view it as a dictionary
		'img_id' is the id of a picture, it is a global unique string key
	return value :
		True means exists, else not exist
	"""
	path="/%s/%s"%(topic,img_id)
	res=conn.exists(path)
	del path
	return res


def get_feature(conn,topic,img_id):
	"""
	get feature(binary) of an image from HDFS

	parameter :
		'conn' is a client object, you can create it by use the above function 'get_conn'
		'topic' is the topic of your files, you can view it as a dictionary
		'img_id' is the id of a picture, it is a global unique string key
	return value :
		binary
	"""
	path="/%s/%s"%(topic,img_id)
	bin_data=None
	f=None
	try:
		f=conn.open(path)
		bin_data=f.read()
	except:
		pass
	finally:
		del path
		if f is not None:
			f.close()
		return bin_data


def get_list_features(conn,topic,img_id_list):
	"""
	get a list of feature(binary) of images from HDFS

	parameter :
		'conn' is a client object, you can create it by use the above function 'get_conn'
		'topic' is the topic of your files, you can view it as a dictionary
		'img_id_list' is a list of ids of pictures
	return value :
		a list, each element is binary
	"""
	bin_list=[]
	for img_id in img_id_list:
		feature_bin=get_feature(conn,topic,img_id)
		if feature_bin is not None:
			bin_list.append(feature_bin)
	return bin_list


def get_all_features(sc,host,port,topic):
	"""
	get the features(binary) of all images from HDFS

	parameter :
		'sc' is a spark context
		'host' is the host of HDFS
		'port' is the port of HDFS (often is 9000)
		'user' is the user of hadoop
		'topic' is the topic of your files, you can view it as a dictionary
	return value :
		a RDD
		each of its element's key is the absolute hdfs path of a file
		each of its element's value is the content of a file
	"""
	path="hdfs://%s:%d/%s"%(host,port,topic)
	return sc.binaryFiles(path)
