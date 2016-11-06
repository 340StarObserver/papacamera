#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	21 July 2016
# Modified 		: 	21 July 2016
# Version 		: 	1.0

"""
This script used to write log
"""

import logging
import datetime

def create_logger(logpath):
	"""
	create a logger

	parameter :
		'logpath' is an absolute path of the log file
	return value :
		a logger
	examples :
		mylogger=create_logger("xxx.log")
		mylogger.debug("your message")
		mylogger.info("your message")
		mylogger.warn("your message")
		mylogger.error("your message")
	"""
	nowstr=datetime.datetime.now().strftime("%Y-%m-%d")
	my_logger=logging.getLogger(nowstr)
	handler=logging.FileHandler(logpath)
	formatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	handler.setFormatter(formatter)
	my_logger.addHandler(handler)
	my_logger.setLevel(10)
	return my_logger
