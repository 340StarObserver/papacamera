## 图片识别业务的部署 ##


        主机A ： master    192.168.0.4      spark主结点，hadoop结点，redis结点，kafka结点，flask结点  
        
        主机B ： slave1    192.168.0.234    spark从结点，hadoop结点  
        
        主机C ： slave2    192.168.0.205    spark从结点，hadoop结点  


        # 在没有特别说明的情况下，默认操作是在主机A上完成的  
        
        # 当前架构，见于architecture.pdf  


### 第一步 ： 为重启服务做清理准备 ###

1，　关闭原先的程序  

        ps -aux | grep main.py  
        
            查看原来的几个进程  
        
        kill -9 进程号  
        
            把上述ps命令结果中列出的进程全部杀戮掉  

2，　关闭redis集群  

        redis-cli -c -h 127.0.0.1 -p 7001 shutdown  
        
            关闭7001的redis结点（注意 -c 参数，以集群方式）  
        
        redis-cli -c -h 127.0.0.1 -p 7002 shutdown  
        
            关闭7002的redis结点（注意 -c 参数，以集群方式）  
        
        redis-cli -c -h 127.0.0.1 -p 7003 shutdown  
        
            关闭7003的redis结点（注意 -c 参数，以集群方式）  

3，　关闭spark集群  

        cd /home/yyz/lib/spark-1.6/sbin  
        
            进入spark的sbin目录  
        
        ./stop-all.sh  
        
            关闭spark集群  

4，　关闭hadoop集群  

        cd /home/yyz/lib/hadoop-2.7.1/sbin  
        
            进入hadoop的sbin目录  
        
        ./stop-yarn.sh  
        
            先关闭yarn集群  
        
        ./stop-dfs.sh  
        
            再关闭dfs集群  

5，　重启每台主机  

        sudo shutdown -r now  
        
            重启当前主机（注意，每台主机都必须要重启）  


### 第二步 ： 清理原先 kafka 的日志和数据（在主结点上操作，必须清理干净，否则收不到消息） ###

        cd /home/yyz/lib/kafka/bin  

            # 进入kafka的bin目录  

        rm -rf /mydata/kafka/data/*  
        rm -rf /mydata/kafka/logs/*  

            # 这两条rm操作，必须在kakfa被关闭后才能做（或重启后），否则下次kafka启动的时候可能报错  
            # 删除之前遗留的kafka的数据与文件  
            # 若不进行删除，则很可能kafka在收取消息的时候会发生一些迷之错误  

### 第三步 ： 启动kafka　& 创建topci（每次重启都要重新创建） ###

        cd /home/yyz/lib/kafka/bin  

            # 进入kafka的bin目录  

        ./zookeeper-server-start.sh /home/yyz/lib/kafka/config/zookeeper.properties &  

            # 启动zookeeper服务（指定了配置文件），注意以后台方式运行  

        ./kafka-server-start.sh /home/yyz/lib/kafka/config/server.properties &  

            # 启动kafka服务（指定了配置文件），注意以后台方式运行  

        jps  

            # 查看java进程，发现Kafka和QuorumPeerMain，则启动成功  

        ./kafka-topics.sh --create --zookeeper 192.168.0.4:2181 --replication 1 --partitions 2 --topic img_msg  

            # 该topic的zookeeper的地址和端口为 192.168.0.4:2181  
            # 该topic的备份数目为 1  
            # 该topic的分区数目为 2  
            # 该topic的名称为 img_msg  
            # 该topic用作把客户端的图片消息转发给spark  

        ./kafka-topics.sh --list --zookeeper 192.168.0.4:2181  

            # 查看topic列表，有且仅有img_msg，说明一切正常  


### 第四步 ： 启动 hadoop ###

        cd /home/yyz/lib/hadoop-2.7.1/sbin  

            # 进入hadoop的sbin目录  

        ./start-dfs.sh  

            # 启动hdfs服务  

        ./start-yarn.sh  

            # 启动yarn服务  

        jps  

            # 发现多出了 ResourceManager，NameNode，SecondaryNameNode，NodeManager，DataNode  
            # 则启动成功  


### 第五步 ： 把新的图片的特征数据入库 ###

        hadoop fs -mkdir /img_feature  

            # 创建一个HDFS目录，用以存放图片的特征数据文件  
            # （如果是第一次的话，需要创建）  
            # （此后重启服务的时候，该步骤就不需要执行了）  

        hadoop fs -mkdir /img_log  

            # 创建一个HDFS目录，用以存放图片识别业务的日志  
            # （如果是第一次的话，需要创建）  
            # （此后重启服务的时候，该步骤就不需要执行了）  

        cd /home/yyz/sparkserver/src/admin  

            # 进入后台管理代码模块  

        python addfeature.py /mydata/program/sparkserver/ads  

            # 注意 ： 首先确保开启了WebHDFS  
            # 注意 ： 在 /mydata/program/sparkserver/ads 这个目录下，存放你这一次想要入库的新的图片们  
            # 注意 ： 图片分辨率必须在550*220左右，图片尺寸在60K左右  
            # （这种情况下，识别率较高，又快）  
            # 该脚本会计算该目录下的所有图片的的特征数据，并存入HDFS  


### 第六步 ： 把原来一些图片的特征数据移除（在你发现原来有些图片大小不合适的时候） ###

        hadoop fs -rm /img_feature/广告的id  
        
            移除某一张广告的特征数据  
            # 移除特征数据，暂时还未提供脚本，需要手动很小心地移除  
            # 此处广告的id是mongodb下对应广告的_id的字符串形式  


### 第七步 ： 启动 spark ###

        cd /home/yyz/lib/spark-1.6/sbin  

            # 进入spark的sbin目录  

        ./start-all.sh  

            # 启动spark  

        jps  

            # 发现多出了 Master，Worker，则启动成功  


### 第八步 ： 启动 redis集群 ###

        cd /home/yyz/lib/redis/restfulshell  

            # 进入事先写好的redis快捷启动的目录  

        ./start.sh  

            # 启动所有的redis示例  

        ./clusterset.sh  

            # 若是第一次启动，需要执行这个脚本，用来初始化集群  

        redis-cli -c -h 127.0.0.1 -p 7001  

            # 连接redis，验证是否启动成功  


### 第九步 ： 启动消费者进程 ###

        cd /home/yyz/sparkserver/src/consumer  

            # 进入消费者代码模块  

        spark-submit --master yarn --deploy-mode client main.py my_group >/dev/null 2>&1 &  

            # 启动spark消费者进程  
            # 注意 ： 以yarn方式运行  
            # 注意 ： 部署方式为client  
            # 注意 ： 不显示标准正常输出与标准错误输出，因为是通过日志文件来记录的  
            # 注意 ： 以后台方式运行  
            # （请记录下进程号，以便kill）  

        cd /mydata/program/sparkserver/consumer  

            # 进入消费者进程的日志目录  

        tail -f 当前日期.log  

            # 查看日志文件，例如 tail -f 20160731.log  
            # 若发现以下字样 ：  

            2016-08-14 11:07:49,872 INFO start consumer program  
            2016-08-14 11:07:49,872 INFO read configuration from ../../conf/server.conf success  
            2016-08-14 11:08:22,738 INFO create spark context success  
            2016-08-14 11:08:23,229 INFO create origin_rdd from HDFS success  
            2016-08-14 11:08:28,133 INFO create shared_rdd based on origin_rdd success  
            2016-08-14 11:08:28,148 INFO connect to redis success  
            2016-08-14 11:08:28,213 INFO connect to mongo success  
            2016-08-14 11:08:28,375 INFO create a kafka consumer success  
            2016-08-14 11:08:28,376 INFO create a oss bucket connect success  
            2016-08-14 11:08:28,376 INFO create a HDFS connect success  
            2016-08-14 11:08:28,377 INFO start to deal with each image request  

            # 则说明消费者程序的初始化成功了  


### 第十步 ： 启动python-webserver ###

        cd /home/yyz/sparkserver/src/web  

            # 进入python-web代码模块  

        python main.py >/mydata/program/sparkserver/webserver/2016xxxx.log 2>&1 &  

            # 启动python-webserver进程  
            # 注意 ： 2016xxxx.log请用当前日期替换，例如20160731.log  
            # 注意 ： 把标准正常输出和标准错误输出，都重定向到这个日志文件  
            # 注意 ： 以后台方式运行  
            # （请记录下进程号，以便kill）  

        cd /mydata/program/sparkserver/webserver  

            # 进入python-webserver的日志目录  

        tail -f 当前日志.log  

            # 查看日志文件，例如 tail -f 20160731.log  
            # 若发现以下字样 ：  

            * Running on http://0.0.0.0:8081/ (Press CTRL+C to quit)  

            # 则说明python-webserver启动成功了  


### 第十一步 ： 验证业务运行 ###

        cd /mydata/program/sparkserver/consumer  

            # 进入消费者进程的日志目录  

        tail -f 当前日期.log  

            # 监控日志输出，例如 tail -f 20160731.log  

        拍摄一张广告上传  

            # 若发现日志文件上出现类似的字样 ：  

            2016-08-14 11:14:30,267 INFO usr:0,time:1471144469,pos:(31.868706,118.828125),res:57a584c1190720c795e4e856,cost:0.422000  

            # 则说明业务正常运行了  
