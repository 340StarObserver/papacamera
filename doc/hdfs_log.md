### hadoop日志与数据文件的迁移 ###


因原来的磁盘容量不够，需要把所有的日志文件与数据文件全部迁移到 /mydata/hadoop/ 下面，  
需要修改的配置文件如下 :  
（每个配置文件中，只要和数据路径日志路径相关的全部改掉）  

* core-site.xml  

* hdfs-site.xml  

* yarn-env.sh  

* mapred-env.sh  

* kms-env.sh  

* httpfs-env.sh  

* hadoop-env.sh  

* httpfs-log4j.properties  

* kms-log4j.properties  

* log4j.properties  

--------------------------------------------------

以 yarn 方式启动hadoop的命令 :  
./start-dfs.sh  
./start-yarn.sh  

使用jps命令，发现DataNode没有起来，查看 /mydata/hadoop/logs/datanodeXXXX.log，  
找到warn的地方，利用warn的信息去查原因，  
发现是因为多执行了一次 hdfs namenode -format，导致datanode,namenode,clusterid出现了不一致，  
所以，我的做法是把日志和数据文件全部删光（反正此时也没数据），然后重新格式化并启动  
