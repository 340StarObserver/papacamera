#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	15 July 2016
# Modified 		: 	12 August 2016
# Version 		: 	1.0

"""
This script used to do something with img feature

you can :
1. calculate the feature of an image
2. serialize the feature to binary format
3. deserialize the feature from binary format
"""

import cv2
import numpy
import cPickle

def calculate_feature(bin_data):
	"""
	calculate the feature data of an image

	parameter :
		'bin_data' is the binary stream format of an image
	return value :
		a tuple of ( keypoints, descriptors, (height,width) )
		keypoints is like [ pt1, pt2, pt3, ... ]
		descriptors is a numpy array
	"""
	buff=numpy.frombuffer(bin_data,numpy.uint8)
	img_obj=cv2.imdecode(buff,cv2.CV_LOAD_IMAGE_GRAYSCALE)
	surf=cv2.FeatureDetector_create("SURF")
	surf.setInt("hessianThreshold",400)
	surf_extractor=cv2.DescriptorExtractor_create("SURF")
	keypoints=surf.detect(img_obj,None)
	keypoints,descriptors=surf_extractor.compute(img_obj,keypoints)
	res_keypoints=[]
	for point in keypoints:
		res_keypoints.append(point.pt)
	del buff
	del surf
	del surf_extractor
	del keypoints
	return res_keypoints,numpy.array(descriptors),img_obj.shape


def serialize(feature_obj):
	"""
	serialize the feature to binary format

	parameter :
		'feature_obj' is like ( keypoints, descriptors, (height,width) )
		keypoints is like [ pt1, pt2, pt3, ... ]
		descriptors is a numpy array
	return value :
		binary
	"""
	return cPickle.dumps(feature_obj)


def deserialize(feature_bin):
	"""
	deserialize the binary format to (keypoints,descriptors)

	parameter :
		'feature_bin' is the binary format of feature data
	return value :
		like ( keypoints, descriptors, (height,width) )
		keypoints is like [ pt1, pt2, pt3, ... ]
		descriptors is a numpy array
	"""
	return cPickle.loads(feature_bin)
