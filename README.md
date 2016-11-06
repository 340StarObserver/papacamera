# papacamera #


基于Spark-Hadoop的户外广告识别系统  
用户通过拍照上传广告图片，服务端识别出是哪张广告并把相关的信息（比如导航，优惠券，商城等）展现给用户  


--------------------------------------------------


### 文档部分 doc/ ###

        doc/architecture.pdf  （ 图片识别业务的架构设计 ）  

        doc/diary.txt  （ 日报 ）  

        doc/mapreduce.md  （ 图片识别业务中 Map-Reduce 的逻辑设计 ）  

        doc/hdfs_log.md  （hadoop数据日志迁移文档）  

        doc/deploy.md  （图片识别业务的部署文档）  

        doc/message_log.md  （消息与日志的设计）  

--------------------------------------------------


### 配置部分 conf/ ###

        conf/server.conf  （ 图片识别业务的配置文件 ）  
        
            # 注意修改相应的配置项  
            # 密钥等信息我已用"******"替换掉了  


--------------------------------------------------


### 公共代码部分 src/common/ ###

        src/common/configure.py  （ 负责读取该业务的配置文件 ）  

        src/common/cache.py  （ 负责操作redis-cluster，读写缓存 ）  

        src/common/feature.py  （负责图片特征数据的计算，序列化，反序列化）  

        src/common/distributedFS.py  （负责操作HDFS）  

            # 注意，需要安装 curl  
            # 注意，需要安装 python的扩展pyhdfs，安装命令 sudo pip install pyhdfs  
            # 注意，需要开启 hadoop的WebHDFS，开启方式是在hadoop的 hdfs-site.xml 中添加 :  
            
                <property>
                    <name>dfs.webhdfs.enabled</name>
                    <value>true</value>
                </property>
                <property>
                    <name>dfs.web.ugi</name>
                    <value>yyz,yyz</value>
                </property>
            # 其中 dfs.web.ugi 这项的值要填启动hadoop的用户和用户组，以逗号隔开  
            

--------------------------------------------------


### web代码部分 src/web/ ###

        src/web/main.py  负责处理来自客户端的图片识别请求  
        
            # run this script :  
            # 1. modify the conf file, which declared in line 30  
            # 2. python main.py >/mydata/program/sparkserver/webserver/2016xxxx.log 2>&1 &  


--------------------------------------------------


### 消费者代码部分 src/consumer/ ###

        src/consumer/main.py  负责从kafka获取图片消息并进行识别  
        
            # 1. 待接入图片识别的函数  
            # 2. 运行方式 spark-submit --master yarn --deploy-mode cluster main.py arg >/dev/null 2>&1 &  

        src/consumer/logger.py  负责记录日志  

        src/consumer/mongoconn.py  负责操作mongo  

        src/consumer/oss.py  负责操作对象存储  

--------------------------------------------------


### 后台管理部分 src/admin/ ###

        src/admin/initkafka.py  负责初始化kafka并创建你想要的topic  

        src/admin/addfeature.py  负责计算新的广告图片的特征数据，并把特征数据入库到HDFS  
