from mqtt_module import mqtt_client, subTopic, pubTopic
import requests
import numpy as np
import cv2
import json
import os
import socket
eqNameDict = {}
# ip:192.168.1.104:002
def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        return ip
local_ip = get_host_ip()
class FaceDetector:
    def __init__(self):
        # 团队服务器ip地址
        self.team_server = "http://42.192.82.19:5555/"

        # 温度阈值，高于这个值就算温度过高
        self.temp_threshold = 37.3

        # 一个管子容纳的核酸检测样本数量，一般都是一个管子有十个样本
        self.pipe_num = 10

    def on_message(self, client, userdata, msg):
        """
        接收到mqtt服务器转发的消息时。执行的函数
        我们只会收到几个话题：
        第一个是小程序想获取所有在线的esp32-cam设备和核酸检测记录。
        第二个是esp32向我们本地服务器发送消息
        :param client: 这个就是外面的那个mqtt_client
        :param userdata: 这个基本上应该没什么用
        :param msg: 这个是接收到的内容。包括收到的消息话题和消息内容
        :return:
        """
        # 消息的内容
        msg_content = str(msg.payload.decode('utf-8'))
        # 这个话题表示esp32发消息给我们，根据消息内容有如下几种情况
        if "IP" not in msg_content:
            print("msg_content=", msg_content)
        if "get_record:" in msg_content:
            """
            此时是小程序想要获取核酸检测信息。我们需要到团队服务器上去请求数据发送给小程序
            """
            return
            # 先从服务器上获取核酸检测记录
            print("get")
            res = requests.get(f"{self.team_server}getRecord/?now={msg_content[11:]}").json()
            # 把从服务器上获取到的核酸检测记录转发给小程序
            res["mode"] = "record"
            # {"mode":"record","list":[{name:"张三",number:"20203231036",healthCode:"正常",temperature:36.2,time:"2023-5-4",result:"阴性"}], "total":1, "now":1}
            self.publish(pubTopic["send2wechat"], json.dumps(res))
        elif msg_content == "online":
            # {"mode":"online", "name":设备名}
            Dict = {}
            Dict['mode'] = "online"
            for name in eqNameDict.keys():
                Dict["name"] = name
                self.publish(pubTopic["send2wechat"], json.dumps(Dict))


        elif "face_recognition:" in msg_content:
            """
            此时是需要对当前esp32-cam捕获的图像进行人脸识别，返回识别结果
            识别结果包括姓名、学/工号、健康码情况（这三个信息暂时存在一个变量里面）
            但是发送回去给esp32的只需要是健康码的情况就行
            """
            # 设备ip地址
            # ip = msg_content[17:msg_content.rfind(":")]
            # 设备名
            eqName = msg_content[msg_content.rfind(":") + 1:]
            # 设备ip地址
            ip = eqNameDict[eqName]
            # esp32会把他的ip地址发送过来，我们根据ip地址就可以从self.ip2request取出对应的request来获取图片
            img = self.rec_img(ip)
            # 把这张图片送到人脸识别算法里面进行人脸识别
            # 这里不一定是一张图片，如果需要的话你可以获取多张图片一起进行一次人脸识别,自行修改（如果这样可以提高识别的准确率的话）
            result = self.face_recognition(img)

            if result is False:
                # 如果没有识别出来的话，给esp32发送None表示没有识别出来
                self.publish(pubTopic['send2esp32'], "face_recognition_result:None")

            else:
                # 如果检测到人的话
                name, number, healthCode = result

                if healthCode == "不正常":
                    # 如果健康码不是绿码也就是不正常，发送给esp32消息False表明健康码不正常
                    self.publish(pubTopic['send2esp32'], "face_recognition_result:False")

                else:
                    # 健康码正常，发送给esp32消息True表明健康码不正常
                    self.publish(pubTopic['send2esp32'], "face_recognition_result:True")

                    # 下面就是把识别到的结果（姓名、号码）记录起来
                    if os.path.exists("testing/" + eqName + ".txt"):
                        file = open("testing/" + eqName + ".json", "r", encoding="utf-8")
                        # 还没出结果的核酸检测记录（也就是正在进行中的核酸检测记录）
                        try:
                            # 如果文件存在且不是空，那就把里面的json格式的内容读出来,是一个列表，列表里面是一个个字典
                            testing_record = json.loads(file.read())
                        except:
                            # 如果文件为空
                            testing_record = []
                        file.close()
                    else:
                        # 如果文件不存在
                        testing_record = []

                    # 向这个列表中添加一条记录
                    testing_record.append({
                        "name": name,
                        "number": number
                    })

                    # 把添加后的列表重新写入json文件中
                    with open("testing/" + eqName + ".json", "w", encoding="utf-8") as file:
                        file.write(json.dumps(testing_record, indent=4, ensure_ascii=False))

        elif "get_temperature:" in msg_content:
            """
            此时是测量完体温了，esp32把体温信息发送给我们
            """
            eqName = msg_content[16:msg_content.rfind(":")]
            temperature = msg_content[msg_content.rfind(":") + 1:]
            # 这里直接读取文件，不错报错处理，因为实际过程中肯定是先人脸识别之后把姓名、号码、健康码状况写入文件后才进行体温测量，所以不可能不存在这个文件或者文件内容为空
            with open("testing/" + eqName + ".json", "r", encoding="utf-8") as file:
                testing_record = json.loads(file.read())

            if int(temperature) > self.temp_threshold:
                # 如果温度过高，就要删除这条记录(也就是最后一条记录)，然后让这个同学去一旁留下观察
                testing_record.pop()

            else:
                # 遍历列表，找到还没有录入温度的那条记录，这个温度就是属于那一条记录的
                for index, each_record in enumerate(testing_record):
                    if each_record.get("temperature") is None:
                        break

                # 这里index飘黄，但是实际正常情况是一定能找到那个index所以如果真的报错就是逻辑有问题
                testing_record[index]["temperature"] = temperature

            # 把添加/删除后的列表重新写入json文件中
            with open("testing/" + eqName + ".json", "w", encoding="utf-8") as file:
                file.write(json.dumps(testing_record, indent=4, ensure_ascii=False))


        elif "get_result:" in msg_content:
            """
            此时是一个管子的核酸检测结果出来了，假设一个管子最多有10个人的核酸检测
            """
            # 设备名
            eqName = msg_content[11:msg_content.rfind(":")]
            # 最新一个管子的核酸检测结果
            result = msg_content[msg_content.rfind(":") + 1:]

            # 这里同样直接读取文件，不进行报错处理，正常情况就不会报错
            with open("testing/" + eqName + ".json", "r", encoding="utf-8") as file:
                testing_record = json.loads(file.read())

            # 给前面的十条记录添加一个result值也就是核酸检测的结果
            tested_record = testing_record[:self.pipe_num]
            for i in range(len(tested_record)):
                tested_record[i]["result"] = result

            # 把这十条已经出结果的核酸检测记录更新到团队服务器上
            res = requests.post(f"{self.team_server}addRecord/", data=json.dumps(tested_record),
                                headers={"content-type": "application/json"})

            # 提醒小程序当前的核酸检测记录已经更新
            self.publish(pubTopic["send2wechat"], '{"mode":"update"}')

            # 删除json文件中前面十条记录（如果少于十条记录那就把剩下的记录删除）
            del testing_record[:self.pipe_num]

            # 把删除后的列表重新写入json文件中
            with open("testing/" + eqName + ".json", "w", encoding="utf-8") as file:
                file.write(json.dumps(testing_record, indent=4, ensure_ascii=False))

        elif msg_content == "get_ip":
            print("发送ip地址给esp32")
            self.publish(pubTopic["send2esp32"], "ip:"+local_ip)
        elif "IP:" in msg_content:
            eqName = msg_content[3:msg_content.rfind(":")]
            ip = msg_content[msg_content.rfind(":")+1:]
            eqNameDict[eqName] = ip
            # data = {}
            # data["eqName"] = eqName
            # data['ip'] = ip
            # print("http://"+local_ip+":8000/getIp/?"+eqName+"="+ip)
            try:
                requests.get("http://"+local_ip+":8000/getIp/?"+eqName+"="+ip)
            except:
                print("出错了")

    def rec_img(self, ip):
        """
        获取esp32当前捕获的图片
        :param ip: 用于获取指定esp32的图片
        :return: esp32当前捕获的图片
        """
        res = requests.get(f"http://{ip}:81/stream", stream=True)
        while True:
            if res.raw.readline() == b'\r\n' and res.raw.readline() == b'--123456789000000000000987654321\r\n':
                res.raw.readline()
                # 图片的字节流的长度
                length = res.raw.readline()[16:-2]
                res.raw.readline()
                # 在这之前都是类似于响应头，这些信息用处不大，除了那个长度，下面这个才是整个图片
                img_data = res.raw.read(int(length))

                array = np.frombuffer(img_data, dtype=np.uint8)

                img = cv2.imdecode(array, cv2.IMREAD_COLOR)
                break
        return img

    def publish(self, topic, msg):
        """
        想topic话题发送消息。消息内容就是msg
        :param topic:
        :param msg:
        :return:
        """
        mqtt_client.publish(topic, msg)

    def face_recognition(self, img):
        """
        输入一张图片进行人脸识别，返回识别的结果
        :param img: 输入的一张图片
        :return: 识别的结果：姓名、学/工号、健康码情况（正常/不正常）,如果图片中没有人脸或者人脸不在数据库中就返回False
        """
        pass


faceDetector = FaceDetector()
mqtt_client.on_message = faceDetector.on_message
mqtt_client.loop_forever()
