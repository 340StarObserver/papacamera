#!/usr/bin/python
# -*- coding:utf-8 -*-

# Author 		: 	Lv Yang
# Created 		: 	21 July 2016
# Modified 		: 	08 August 2016
# Version 		: 	1.0

"""
This script used to initialize kafka and create a topic for image messages
"""

import sys
import string

sys.path.append("../common")
import configure


def entrance(confpath):
	"""
	print detail commands of how to initialize the Kafka
	parameter :
		'confpath' is path of the configure file
	"""
	conf=configure.read(confpath)
	inform="This script show how to initialize the Kafka,\
		\r\nyou should execute the following commands :\
		\r\n\r\n1. stop kafka\
		\r\n\tcd %s\
		\r\n\t./kafka-server-stop.sh\
		\r\n\t./zookeeper-server-stop.sh\
		\r\n\t# if you find can't stop kafka,\
		\r\n\t# but when you use jps, you really find kafka,\
		\r\n\t# you should reboot the system to force to stop kafka\
		\r\n\r\n2. delete kafka's data and logs\
		\r\n\trm -rf %s/*\
		\r\n\trm -rf %s/*\
		\r\n\t# if don't delete data and logs,kafka may can't receive messages\
		\r\n\r\n3. start kafka\
		\r\n\tcd %s\
		\r\n\t./zookeeper-server-start.sh %s/zookeeper.properties &\
		\r\n\t./kafka-server-start.sh %s/server.properties &\
		\r\n\r\n4. create a topic for forwarding image messages\
		\r\n\tcd %s\
		\r\n\t./kafka-topics.sh --create --zookeeper %s --replication-factor 1 --partitions 2 --topic %s\
		\r\n\r\n5. create a topic for forwarding result logs\
		\r\n\t./kafka-topics.sh --create --zookeeper %s --replication-factor 1 --partitions 2 --topic %s"\
		%(conf['kafka']['binpath'],conf['kafka']['datapath'],conf['kafka']['logpath'],\
		conf['kafka']['binpath'],conf['kafka']['confdir'],conf['kafka']['confdir'],\
		conf['kafka']['binpath'],conf['kafka']['zookeeper'],conf['kafka']['topic'],\
		conf['kafka']['zookeeper'],conf['resultlog']['kafka_topic'])
	print inform


if __name__ == '__main__':
	entrance("../../conf/server.conf")
