## 图片识别业务中的消息和日志 ##


### 1. 图片识别请求的消息 ###

        谁写 : python-webserver  
        
        写至 : kafka 中的名为 img_msg 的topic  

            # 消息的 key   :  

                request_key,userid,pos_x,pos_y  
                
                形如 "1445599887abcdefgh,340,10.55,20.16"  

            # 消息的 value :  

                图片的二进制数据  

        谁读 : spark   


### 2. 图片识别结果的日志 ###

        1. 首先，记录每张客户端传来的照片  

            使用对象存储来保存每张照片，bucket的名字为papacamera  
        
            该bucket下的img_log文件夹下，每天一个子文件夹  
        
            例如某个图片是 img_log/20160817/1445599887abcdefgh.jpg  


        2. 然后，每个客户端照片的识别结果的日志格式  

            {  
                usr  : 用户id（若没有，则为零）,  
            
                time : 用户上传图片的时间戳,  
            
                x    : 拍摄地点的x坐标（若没有，则为200）,  
            
                y    : 拍摄地点的y坐标（若没有，则为200）,  
            
                img  : 此图片在oss中的位置（例如 img_log/20160817/1445599887abcedfgh.jpg）,  
            
                res  : 识别出的广告id（若没有识别出来，则为"None"）,  
            
                cost : 识别用时(秒)  
            }  


        3. 最后，日志是累积到一定数目，批量写入HDFS  
