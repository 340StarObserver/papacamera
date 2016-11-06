#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	21 July 2016
# Modified 		: 	05 August 2016
# Version 		: 	1.0

"""
This script used to push images feature data into HDFS
"""

import sys
import os

sys.path.append("../common")
import configure
import feature
import distributedFS

def help():
	"""show help of how to run this script"""
	inform="This script used to push images' feature into HDFS\
		\r\nusage :\
		\r\n\tpython addfeature.py arg\
		\r\nparameter :\
		\r\n\targ : the directory of images which you want to put into HDFS\
		\r\n\t# make sure that your images' like object_id1.jpg, object_id2.png ...\
		\r\n\t# object_idi is the ObjectId of an advertisement document in mongodb\
		\r\nexample :\
		\r\n\tpython addfeature.py /mydata/program/sparkserver/ads"
	print inform


def add_one_feature(hdfs_conn,hdfs_topic,img_path):
	"""
	push one image's feature data into HDFS

	parameters :
		'hdfs_conn' is a client object, you can create it by pyhdfs.HdfsClient
		'hdfs_topic' is the directory in HDFS where you want to place feature data
		'img_path' is the path of the source image
	"""
	try:
		img_id=os.path.basename(img_path).split('.')[0]
		if distributedFS.exist_feature(hdfs_conn,hdfs_topic,img_id):
			print "warning : %s already exists in HDFS"%(img_id)
		else:
			f=open(img_path,"rb")
			img_data=f.read()
			f.close()
			feature_bin=feature.serialize(feature.calculate_feature(img_data))
			distributedFS.put_feature(hdfs_conn,hdfs_topic,img_id,feature_bin)
			print "info : put %s feature data into HDFS success, its id is %s"%(img_path,img_id)
	except Exception,e:
		print "error : fail to deal with %s, reason is :"%(img_path)
		print str(e)


def entrance(confpath):
	# get path of image files
	img_files=[]
	try:
		img_directory=sys.argv[1]
		img_files=os.listdir(img_directory)
		n=len(img_files)
		i=0
		while i<n:
			img_files[i]="%s/%s"%(img_directory,img_files[i])
			i+=1
	except Exception,e:
		print str(e)
		help()
		sys.exit(1)
	
	# read configuration
	conf=configure.read(confpath)

	# create a client of HDFS
	conn=None
	try:
		conn=distributedFS.get_conn(conf['hadoop']['hosts'],conf['hadoop']['username'])
	except Exception,e:
		print str(e)
		sys.exit(1)

	# deal with each image
	for img_path in img_files:
		add_one_feature(conn,conf['hadoop']['topic'],img_path)


if __name__ == '__main__':
	entrance("../../conf/server.conf")
