import paho.mqtt.client as mqtt

HOST = "bemfa.com"
PORT = 9501
client_id = "0c90e6e868154d44b6b3df9e90b24543"
# 订阅的话题
subTopic = "1"
# 我们会用到的几个用于发布的话题
pubTopic = {
    "send2wechat": "0",
    "send2esp32": "2"
}

"""
  
"""
#{"mode":"record","list":[{name:"张三",number:"20203231036",healthCode:"正常",temperature:36.2,time:"2023-5-4",result:"阴性"}], "total":1, "now":1}
"""
涉及的话题：
0-小程序订阅（本地服务器或esp32的）消息，可能的消息内容如下
    消息内容为<{"mode":"record","list":核酸检测记录列表, "total":1, "now":1}> 表示本地服务器将核酸检测记录（也就是这个对象）发送给小程序,total是总共有多少页，now是当前是第几页
    消息内容为<{"mode":"online", "name":设备名}> 表示一个esp32回复自己是在线的
    消息内容为<{"mode":"update", "list":核酸检测记录列表, "total":1, "now":1}>表示本地服务器提醒小程序当前核酸检测记录已经更新并发送最新的核酸检测记录
    
1-本地服务器订阅（小程序或esp32的）消息，可能的消息内容如下
    消息内容为<get_record:页码> 表示小程序想获取截至目前的所有核酸检测记录中某一页，
    消息内容为<face_recognition:设备名> 表示esp32请求本地服务器对它当前的图片进行人脸识别
    消息内容是<get_temperature:设备名:温度> 表示esp32将温度发送给本地服务器
    消息内容是<get_result:设备名:核酸检测结果> 表示esp32(不一定是esp32，也可能是其他设备，反正要知道设备名) 把最终核酸检测的结果发送给本地服务器
    消息内容是<get_ip>表示esp想要获取本地服务器的ip地址
    消息内容是<IP:ip地址:设备名>表示esp想要获取本地服务器的ip地址
    
2-esp32订阅消息，根据消息内容来判断是要测试在线情况、人脸识别等等情况
    消息内容为<online>表示小程序想要测试esp32的在线情况
    消息内容为<face_recognition_result:结果> 表示本地服务器把人脸识别的结果（健康码的情况）发送给esp32.想让它转发给合泰单片机
    消息内容为<face_recognition>表示合泰想对当前这个esp32捕获的图片进行人脸识别（串口）
    消息内容为<get_temperature:温度> 表示合泰把温度发给esp32想让它把温度转发给本地服务器（串口）
    消息内容为<ip:ip地址> 表示本地服务器把ip地址发给他了
"""
"""
esp32上电发送ip地址以及设备名给服务器也就是话题1。本地服务器收到后保存到一个字典里面。
"""


# 连接并订阅
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # 订阅消息
    client.subscribe(subTopic)


# 订阅成功
def on_subscribe(client, userdata, mid, granted_qos):
    print("On Subscribed: qos = %d" % granted_qos)


# 失去连接
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection %s" % rc)


mqtt_client = mqtt.Client(client_id)
# 设置账号密码
mqtt_client.username_pw_set("3021535658", "123456")
mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect(HOST, PORT, 60)
