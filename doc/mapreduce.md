## 图片识别业务中 Map-Reduce 的逻辑设计 ##

--------------------------------------------------


### 启动 spark 时 ###

1， 以库中的所有特征数据构造出一个大的特征数据RDD，记为 origin_rdd  

            使用 SparkContext类的binaryFiles方法，加载 HDFS中的所有特征数据文件  

            # 这样一来，这个 origin_rdd 中的每个元素形如 ：  
            # ( 特征数据路径, 序列化的特征数据 )  
            # 特征数据路径 ： 完整的HDFS路径，例如 hdfs://master:9000/img_feature/object_id  
            # 序列化的特征数据 ： 二进制字节流形式的  
                
2， shared_rdd = origin_rdd.map(f)  

            # 这个 f 形如 :  

            def f(element):  
                key=os.path.basename(element[0])  
                value=cPickle.loads(element[1])  
                return (key,value)  

            # 即 :  
            # 先变换 key :  
            # 例如把 hdfs://host:port/img_feature/object_id 转化为 object_id  
            # 再变换 value :  
            # 把二进制的特征数据 转化为 反序列化后的特征数据  

            # 综上 :  
            # 此次map，把原来origin_rdd中的每个元素，由 ( 特征数据完整路径, 序列化的特征数据 ) 转化为 ( 特征数据id, 特征数据 )  
            # 并生成一个新的RDD，名为 shared_rdd  
            # 这样一来，shared_rdd中的特征数据就形如 ( keypoints, descriptors, (height,width) )  
            # 其中，keypoints 形如 [ pt1, pt2, pt3, ... ]  
            # 其中，descriptors 是一个numpy数组  

3， shared_rdd.persist(storageLevel=StorageLevel.MEMORY_AND_DISK)  

            将这个 shared_rdd 持久化  

            # 因为这个RDD是所有客户端请求所公用的，所以需要持久化来达到重复利用的目的  
            # 因为这个RDD可能很巨大，所以不能仅仅持久化到内存，需要内存与磁盘兼用  

4， shared_rdd.reduce(g)  

            对 shared_rdd 做一次无谓的Action  
            这个 g 形如 :  

            def g(elementA,elementB):  
                return elementA  

            # 因为 shared_rdd 的持久化，是惰性求值的，也就是说，在真正做一次Action之前，它不会真的进行持久化  
            # 所以，这边我进行了一次无谓的reduce，来使得持久化生效  

5， 删除 origin_rdd  

            origin_rdd.unpersist()  
            del origin_rdd  
            # 之后不再需要origin_rdd了，而且它也十分巨大，所以及时删除它  
            # 单单del对象是不行的，需要手动unpersist  

6， 不断从Kafka中拿出消息  

        # 注意，不能使用 spark-streaming　的方式  
        # 因为 spark-streaming　也会产生RDD（这个RDD是图片消息的rdd，并非上述论及的shared_rdd）  
        # 所以，你在处理每条客户端的图片消息的时候，实际上处理图片消息可能已经是在slave上了  
        # 这个时候，你再想去拿刚才的 shared_rdd 做 map和reduce，已经是无法做到的了，因为slave无法把shared_rdd分发出去  
        # 也就是说，在你拿到一个图片消息后，想要分发shared_rdd，必须要求那个时刻图片消息在master手中  
        # 而要保证图片消息在master手中，就不能采用spark-streaming的方式，只能用 非streaming 的方式  

--------------------------------------------------


### 每当从 Kafka 中读取一个图片消息 ###

1， 计算这张图片的特征数据  

            假设从Kafka中收到的图片消息的值，记为img_data  
            使用 src/common/feature.py 中的 calculate_feature函数，计算特征数据  
            记为 C = calculate_feature(img_data)  
            
            # C 形如 ( keypoints, descriptors, (height,width) )  
            # 其中，keypoints 形如 [ pt1, pt2, pt3, ... ]  
            # 其中，descriptros 是一个numpt数组  
 
2， analyzed_rdd = shared_rdd.map(my_map)  

            # 这个 my_map 能够闭包地去使用C  
            # 这个 my_map 形如 :  

            def my_map(element):  
                value=match(C, element[1])  
                return (element[0],value)  
            
            # 此处的 match 函数形如 :  
            
            def match(featureA,featureB):  
                flann_params=dict(algorithm=1,trees=5)  
                matcher=cv2.FlannBasedMatcher(flann_params,{})  
                然后使用 matcher, featureA, featureB 计算出一个 bool值  
                并返回这个bool值  

            # 这个 match 函数是通过 比对 客户图片特征数据 和 当前图片特征数据， 并返回比对结果  
            # 其中的参数 featureA 和 featureB 都是特征数据，形如 ( keypoints, descriptors, (height,width) )  
            # 其中，keypoints 形如 [ pt1, pt2, pt3, ... ]  
            # 其中，descriptors 是一个numpy数组  
            # 这个 match 函数的返回值表示是否匹配到（True表示匹配到，False表示没有匹配到）  
            
            # 综上 ：  
            # my_map 把 shared_rdd 中每个元素，从原来的 ( 图片id, 特征数据 ) 转变为 ( 图片id, 是否匹配到 )  
            # 并且生成一个全新的 analyzed_rdd  

3， final_element = analyzed_rdd.reduce(my_reduce)  

            # 这个 my_reduce 用来选出最终的匹配结果  
            # 这个 my_reduce 形如 ：  

            def my_reduce(elementA, elementB):  
                if elementA[1] is True:  
                    return elementA  
                else:  
                    return elementB  

            # 若elementA和elementB都是匹配到的，则取前者    

4， 删除analyzed_rdd  

            analyzed_rdd.unpersist()  
            del analyzed_rdd
            # 此后不再需要这个analyzed_rdd了，及时删除它  
            # 单单del对象是不行的，需要手动unpersist  

5， 取出最终匹配到的图片id  

            img_id = None  
            if final_element[1] is True:  
                img_id = final_element[0]  

            # 若最终的 img_id 不为None，则表明有图片被匹配到了，再利用这个img_id去查出该图片对应的广告的详细信息  
