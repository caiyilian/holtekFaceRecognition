import paho.mqtt.client as mqtt

HOST = "bemfa.com"
PORT = 9501
client_id = "0c90e6e868154d44b6b3df9e90b24543"
# 订阅的话题
subTopic = {
    "wechat_get_info": "2",
    "get_ip": "3",
    "face_recognition": "4",
    "get_temperature": "5"
}
# 我们会用到的几个用于发布的话题
pubTopic = {
    "send_equipment_wechat": "0",
    "send_recordedInfo_wechat": "1",
    "test_esp32_online": "6",

}


# 连接并订阅
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("2")  # 订阅消息


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
