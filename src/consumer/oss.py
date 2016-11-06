#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	06 August 2016
# Modified 		: 	09 August 2016
# Version 		: 	1.0

"""
This script used to operate Object-Oriented Storage
"""

import oss2

def get_bucket(access_id,access_key,oss_host,oss_bucket):
	"""
	create a bucket object

	parameters :
		'access_id' is the AccessKeyId
		'access_key' is the AccessKeySecret
		'oss_host' is the host of your OSS
		'oss_bucket' is the bucket name
	"""
	auth=oss2.Auth(access_id,access_key)
	bucket=oss2.Bucket(auth,oss_host,oss_bucket)
	return bucket

def add_object(bucket_obj,object_name,bin_data):
	"""
	add an object to OSS

	parameters :
		'bucket_obj' is a bucket object, you can create it by oss2.Bucket
		'object_name' is the name of your object
		'bin_data' is the binary format of an object which you want to add into OSS
	"""
	result=bucket_obj.put_object(object_name,bin_data)
	return (result.status,result.request_id,result.etag)
