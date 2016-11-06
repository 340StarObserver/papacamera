#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	20 July 2016
# Modified 		: 	12 August 2016
# Version 		: 	1.0

"""
This script fetch messages from Kafka and do image match

run this script :
1. modify the conf file, which declared in line 564
2. spark-submit --master yarn --deploy-mode client main.py arg >/dev/null 2>&1 &
"""

import sys
import os
import datetime
import time
import cPickle
import cv2
import numpy
import json
import base64

from pyspark import SparkContext
from pyspark import StorageLevel
from kafka import KafkaConsumer

sys.path.append("../common")
import configure
import cache
import distributedFS
import feature
import logger
import mongoconn
import oss


def filter_matches(queryKeypoints, trainKeypoints, KeypointMatches, ratio=0.75):
	"""
	filter_matches(...) : filter the matched keypoints. If the distance of the nearest point is far
	 		from the second nearest point by a set ratio, then this point will be the good one.
		queryKeypoints: keypoints of the query image
		trainKeypoints: keypoints of the train image
		matches: raw matches with knnMatch(...).
	return: the good matched keypoints of query image keypoints and train image keypoints.
	"""
	mkp1,mkp2 = [],[]
	for m in KeypointMatches:
		if len(m) == 2 and m[0].distance < m[1].distance * ratio:
			m = m[0]
			mkp1.append(queryKeypoints[m.queryIdx])
			mkp2.append(trainKeypoints[m.trainIdx])
	queryGoodKeypoints = numpy.float32(mkp1)
	trainGoodKeypoints = numpy.float32(mkp2)
	del mkp1
	del mkp2
	return queryGoodKeypoints, trainGoodKeypoints


def matchFeatures(queryFeature, trainFeature, matcher):
	"""
	match(...) function: match query image features and train image features.
	parameter:
		queryFeature: features of query image
		trainFeature: features of train image
		matcher:      feature matcher
		queryImage:   this is just for test to show the position of the found image which in the query image
		              , input query image data which has processed by cv2.imread().
	return:
		if found matched image ,return image name, otherwise return None.
	"""
	queryKeypoints = queryFeature[0]
	queryDescriptors = queryFeature[1]

	trainKeypoints = trainFeature[0]
	trainDescriptors = trainFeature[1]
	trainImgSize = trainFeature[2]
	trainImgHeight = trainImgSize[0]
	trainImgWidth = trainImgSize[1]

	corners=numpy.float32([[0, 0], [trainImgWidth, 0], [trainImgWidth, trainImgHeight], [0, trainImgHeight]])
	raw_matches = matcher.knnMatch(trainDescriptors, queryDescriptors, 2)
	queryGoodPoints, trainGoodPoints = filter_matches(trainKeypoints, queryKeypoints, raw_matches)

	if len(queryGoodPoints) >= 4:
		H,status = cv2.findHomography(queryGoodPoints, trainGoodPoints, cv2.RANSAC, 5.0)
	else:
		H,status = None,None
	res=False
	obj_corners=None
	if H is not None:
		corners = corners.reshape(1, -1, 2)
		obj_corners = numpy.int32(cv2.perspectiveTransform(corners, H).reshape(-1, 2))
		is_polygon = ispolygon(obj_corners)
		if is_polygon:
			res=True
	del queryKeypoints
	del queryDescriptors
	del trainKeypoints
	del trainDescriptors
	del trainImgSize
	del corners
	del raw_matches
	del queryGoodPoints
	del trainGoodPoints
	del obj_corners
	return res


def absCosVector(v1, v2):
	"""
	calculate absolute value of cosine between two vector v1 and v2
	"""
	l = len(v1)
	result1 = 0.0
	result2 = 0.0
	result3 = 0.0

	if(len(v1) != len(v2)):
		return -9

	i=0
	while i<l:
		result1 += v1[i]*v2[i]
		result2 += v1[i]**2
		result3 += v2[i]**2
		i+=1
	if result2 == 0 or result3 == 0:
		return -10
	else:
		absCosVec = abs(result1 / ((result2 * result3) ** 0.5))
		return absCosVec


def vector(p1,p2):
	if len(p1) == len(p2):
		v = []
		n=len(p1)
		i=0
		while i<n:
			v.append(p1[i]-p2[i])
			i+=1
		return v
	else:
		return


def ispolygon(points):
	"""
	Judge if the given points is polygon-like.
	"""
	if isConvexQuadrilateral(points):
		vec1 = vector(points[0], points[1])
		vec2 = vector(points[0], points[3])
		vec3 = vector(points[1], points[2])
		vec4 = vector(points[2], points[3])

		absCos = []
		absCos.append(absCosVector(vec1, vec2))
		absCos.append(absCosVector(vec1, vec3))
		absCos.append(absCosVector(vec1, vec4))
		absCos.append(absCosVector(vec2, vec4))
		absCos.append(absCosVector(vec2, vec3))
		absCos.append(absCosVector(vec3, vec4))
		approxVertical, approxHorizontal = 0, 0
		for cosine in absCos:
			if cosine < 0.26:
				approxVertical = approxVertical + 1
			if cosine >= 0.95 and cosine <= 1:
				approxHorizontal = approxHorizontal + 1
		del vec1
		del vec2
		del vec3
		del vec4
		del absCos
		if approxVertical >= 2 and approxVertical <= 4 and approxHorizontal >= 1 and approxHorizontal <= 2:
			return True
		else:
			return False
	else:
		return False


def isConvexQuadrilateral(points):
	"""
	Judge if the given points is convex quadrilateral.
	"""
	(x1, y1), (x2, y2), (x3, y3), (x4, y4) = points

	if x1 != x3:
		k1, b1 = pointSlopeForm(points[0], points[2])
		togather1 = isTogather(k1, b1, points[1], points[3])
	else:
		b = x1
		togather1 = isTogather2(b, points[1], points[3])

	if x2 != x4:
		k2, b2 = pointSlopeForm(points[1], points[3])
		togather2 = isTogather(k2, b2, points[0], points[2])
	else:
		b = x2
		togather2 = isTogather2(b, points[0], points[2])

	return togather1 and togather2


def pointSlopeForm(point1, point2):
	"""
	Calculate the point-slope form of straight line between point1 and point2.
	"""
	(x1, y1) = point1
	(x2, y2) = point2
	if x1 != x2:
		k = float((y2 - y1)) / float((x2 - x1))
		b = y1 - k * x1

	return k, b


def isTogather(k, b, point1, point2):
	"""
	Judge if point1 and point2 is at the same side of the diagonal when the diagonal is NOT x = b.
	"""
	(x1, y1) = point1
	(x2, y2) = point2
	v1 = int(y1 - k * x1 - b)
	v2 = int(y2 - k * x2 - b)

	if v1 != 0 and v2 != 0:
		if v1^v2 < 0:
			return  True
		else:
			return False
	else:
		return False


def isTogather2(b, point1, point2):
	"""
	Judge if point1 and point2 is at the same side of the diagonal when the diagonal is x = b.
	"""
	(x1, y1) = point1
	(x2, y2) = point2
	v1 = int(x1 - b)
	v2 = int(x2 - b)

	if v1 != 0 and v2 != 0:
		if v1^v2 < 0:
			return  True
		else:
			return False
	else:
		return False


def match(query_feature, train_feature):
	"""
	calculate some match result between two images' feature data

	parameter :
		'query_feature' is one image's feature data
		'train_feature' is another image's feature data
		both like ( keypoints, descriptros, (height,width) )
		keypoints is like [ pt1, pt2, pt3, ... ]
	return value :
		True of False
	steps :
		1. create a matcher
		2. do match
	"""
	flann_params = dict(algorithm=1, trees=5)
	matcher = cv2.FlannBasedMatcher(flann_params,{})
	res=matchFeatures(query_feature, train_feature, matcher)
	del flann_params
	del matcher
	return res


# function used to get current milli timestamp
def get_milli_time():
	return int(round(time.time() * 1000))/1000.0


def msg_handler(msg_key,msg_value,rdd,redis_conn,log_writer,conf,mongo_client,oss_conn,hdfs_conn,log_container):
	"""
	deal with each message

	parameter :
		'msg_key' is the key of a message
		'msg_value' is the value(binary format of an image) of a message
		'rdd' is the shared_rdd
		'redis_conn' is the connect to redis cluster
		'log_writer' is the logger
		'conf' is the configuration
		'mongo_client' is a client of mongodb
		'oss_conn' is a oss bucket connect
		'hdfs_conn' is a HDFS client
		'log_container' is a string list
	"""
	# split the message key
	request_id=None
	user_id=0
	pos_x=200
	pos_y=200
	try:
		words=msg_key.split(',')
		request_id=words[0]
		user_id=int(words[1])
		pos_x=float(words[2])
		pos_y=float(words[3])
	except Exception,e:
		log_writer.error("fail to split message key")
		log_writer.error(str(e))
		return

	# calculate feature data of the client image
	calc_start=get_milli_time()
	feature_data=None
	try:
		feature_data=feature.calculate_feature(msg_value)
	except Exception,e:
		log_writer.error("fail to calculate feature data of the client image")
		log_writer.error(str(e))
	if feature_data is None:
		log_writer.error("img_id is None because failed to calculate feature data")
		cache.set(redis_conn,request_id,'{}',conf['redis']['expire'])
		return

	def match_map(element):
		value=match(feature_data,element[1])
		return (element[0],value)

	def match_reduce(elementA,elementB):
		if elementA[1] is True:
			return elementA
		else:
			return elementB

	# do map
	analyzed_rdd=rdd.map(match_map)

	# do reduce
	img_id=None
	try:
		final_element=analyzed_rdd.reduce(match_reduce)
		if final_element[1] is True:
			img_id=final_element[0]
	except Exception,e:
		log_writer.error(str(e))
	calc_end=get_milli_time()

	# search info from mongodb by the img_id
	ad_info='{}'
	result_log="usr:%d,time:%s,pos:(%f,%f),res:%s,cost:%f"%(\
		user_id,request_id[0:10],pos_x,pos_y,str(img_id),calc_end-calc_start)
	log_writer.info(result_log)
	try:
		if img_id is not None:
			ad_info=mongoconn.get_one(mongo_client,\
				conf['mongo']['dbname'],\
				conf['mongo']['collection'],\
				img_id)
			ad_info=json.dumps(ad_info)
	except Exception,e:
		log_writer.error(str(e))

	# write ad_info to redis cluster
	cache.set(redis_conn,request_id,ad_info,conf['redis']['expire'])

	# send image to oss
	time_str=datetime.datetime.now().strftime("%Y%m%d")
	obj_name="%s/%s/%s.jpg"%(conf['oss']['oss_dir'],time_str,request_id)
	try:
		oss.add_object(oss_conn,obj_name,msg_value)
		one_log='{"usr":%d,"time":"%s","x":%f,"y":%f,"img":"%s","res":"%s","cost":%f}\n'%(\
			user_id,request_id[0:10],pos_x,pos_y,obj_name,str(img_id),calc_end-calc_start)
		log_container.append(one_log)
		del one_log
	except Exception,e:
		log_writer.error(str(e))

	# write logs to HDFS
	if len(log_container)==conf['resultlog']['batch_size']:
		hdfs_path="/%s/%s.log"%(conf['resultlog']['hdfs_topic'],time_str)
		batch_logs="".join(log_container)
		try:
			if hdfs_conn.exists(hdfs_path) is False:
				hdfs_conn.create(hdfs_path,batch_logs)
			else:
				hdfs_conn.append(hdfs_path,batch_logs)
		except Exception,e:
			log_writer.error(str(e))
		finally:
			del hdfs_path
			del batch_logs
			del log_container[:]

	# finally delete some objects
	analyzed_rdd.unpersist()
	del analyzed_rdd
	del request_id
	del img_id
	del ad_info
	del result_log
	del time_str
	del obj_name


def entrance(confpath,groupid):
	"""
	parameters :
		'confpath' is the path of conf file
		'groupid' is the name of the kakfa consumer's group
	"""
	# read configuration
	config=configure.read(confpath)

	# create a logger
	logpath="%s/%s.log"%(config['consumer']['logpath'],\
		datetime.date.today().strftime("%Y%m%d"))
	log_writer=logger.create_logger(logpath)
	log_writer.info("start consumer program")
	log_writer.info("read configuration from %s success"%(confpath))

	# create spark context
	sc=None
	try:
		sc=SparkContext(appName=config['consumer']['app_name'])
	except Exception,e:
		log_writer.error("fail to create spark context")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create spark context success")

	# create origin_rdd from HDFS
	origin_rdd=None
	try:
		origin_rdd=distributedFS.get_all_features(sc,\
			config['hadoop']['hdfs_host'],\
			config['hadoop']['hdfs_port'],\
			config['hadoop']['topic'])
	except Exception,e:
		log_writer.error("fail to create origin_rdd from HDFS")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create origin_rdd from HDFS success")

	def origin_map(element):
		"""
		map key from hdfs://host:port/path/object_id to object_id
		map value from binary to ( keypoints, descriptors, (height,width) )
		"""
		key=os.path.basename(element[0])
		value=cPickle.loads(element[1])
		return (key,value)

	def origin_reduce(elementA,elementB):
		"""
		this action just to make persist useful
		"""
		return elementA

	# create shared_rdd
	shared_rdd=None
	try:
		shared_rdd=origin_rdd.map(origin_map)
		shared_rdd.persist(storageLevel=StorageLevel.MEMORY_AND_DISK)
		shared_rdd.reduce(origin_reduce)
		origin_rdd.unpersist()
		del origin_rdd
	except Exception,e:
		log_writer.error("failed to create shared_rdd based on origin_rdd")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create shared_rdd based on origin_rdd success")

	# create a connection to redis cluster
	redis_conn=None
	try:
		redis_conn=cache.get_conn(config['redis']['servers'])
	except Exception,e:
		log_writer.error("fail to connect redis cluster")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("connect to redis success")

	# create a connect to mongodb
	mongo_client=None
	try:
		mongo_client=mongoconn.get_conn(config['mongo']['hosts'],\
			config['mongo']['user'],\
			config['mongo']['pwd'],\
			config['mongo']['dbname'])
	except Exception,e:
		log_writer.error("fail to connect mongo")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("connect to mongo success")

	# create a kafka consumer
	consumer=None
	try:
		consumer=KafkaConsumer(config['kafka']['topic'],\
			group_id=groupid,\
			bootstrap_servers=config['kafka']['servers'])
	except Exception,e:
		log_writer.error("fail to create a kafka consumer")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create a kafka consumer success")

	# create a oss bucket connect
	oss_bucket_conn=None
	try:
		oss_bucket_conn=oss.get_bucket(config['oss']['access_id'],\
			config['oss']['access_key'],\
			config['oss']['host'],\
			config['oss']['bucket'])
	except Exception,e:
		log_writer.error("fail to create a oss bucket connect")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create a oss bucket connect success")

	# create a HDFS connect
	hdfs_conn=None
	try:
		hdfs_conn=distributedFS.get_conn(config['hadoop']['hosts'],\
			config['hadoop']['username'])
	except Exception,e:
		log_writer.error("fail to create a HDFS connect")
		log_writer.error(str(e))
		sys.exit(1)
	log_writer.info("create a HDFS connect success")

	# deal with messages one by one
	log_writer.info("start to deal with each image request")
	log_container=[]
	for message in consumer:
		msg_handler(message.key,message.value,\
			shared_rdd,redis_conn,log_writer,config,mongo_client,\
			oss_bucket_conn,hdfs_conn,log_container)
		del message


def help():
	"""
	show how to run this script
	"""
	inform="This script is the consumer program to deal with images\
		\r\nusage :\
		\r\n\tspark-submit --master yarn --deploy-mode client main.py arg >/dev/null 2>&1 &\
		\r\n\t( this 'arg' is the group id of kafka consumer,it is determined by you )"
	print inform


if __name__=='__main__':
	if len(sys.argv)<2:
		help()
	else:
		entrance("../../conf/server.conf",sys.argv[1])
