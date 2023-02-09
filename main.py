from mqtt_module import mqtt_client, subTopic, pubTopic
import requests
import numpy as np
import cv2


class FaceDetector:
    def __init__(self):
        # 这个字典用于将esp32的ip地址对应一个request。这个request可用于请求esp32当前捕获的图片
        self.ip2request = {}

    def on_message(self, client, userdata, msg):
        """
        接收到mqtt服务器转发的消息时。执行的函数
        我们只会收到几个话题：
        第一个是小程序想获取所有在线的esp32-cam设备和核酸检测记录。
        第二个是esp32-cam刚开机的时候。会把ip地址发送给我们。
        第三个是esp32-cam请求进行人脸识别
        第四个是esp32-cam发送体温给我们
        第五个是esp32-cam把返回他们的在线信息
        :param client: 这个就是外面的那个mqtt_client
        :param userdata: 这个基本上应该没什么用
        :param msg: 这个是接收到的内容。包括收到的消息话题和消息内容
        :return:
        """
        # 消息的主题
        msg_topic = msg.topic
        # 消息的内容
        msg_content = str(msg.payload.decode('utf-8'))
        if msg_topic == subTopic["wechat_get_info"]:
            """
            此时某个设备的小程序刚开启。他想要获取目前所有在线的esp32-cam和累计到现在的所有核酸检测记录
            获取所有在线的esp32-cam很简单。只需要对一个用于测试当前设备在线个数的话题发送信息，查看给定时间范围内回复的消息数量就行
            获取所有核酸检测记录的话。只需要请求我们团队的服务器即可。我打算把所有核酸检测记录存放在我们团队的服务器上面
            """
            # 先向所有esp32-cam发送测试消息。如果他们在线的话就会回复，话题是指定的，但是内容随便，所以这里内容就随便写了个12138
            self.publish(pubTopic["test_esp32_online"], "12138")
            # 第二步向我们团队服务器请求获取所有核酸检测记录，并把这些记录发送给小程序
            pass

        elif msg_topic == subTopic["get_ip"]:
            """
            此时是某个esp32-cam刚开机。然后他会把他的ip地址发送给我们,此时msg_content就是它的ip地址
            我们需要做的就是把这个ip地址存起来，放在self.ip2request这个字典里面，便于我们后面调用
            """
            self.ip2request[msg_content] = requests.get(f"http://{msg_content}:81/stream", stream=True)

        elif msg_topic == subTopic["face_recognition"]:
            """
            此时是需要对当前esp32-cam捕获的图像进行人脸识别，返回识别结果
            识别结果包括姓名、学/工号、健康码情况
            """
            # esp32会把他的ip地址发送过来，我们根据ip地址就可以从self.ip2request取出对应的request来获取图片
            img = self.rec_img(self.ip2request[msg_content])
            # 把这张图片送到人脸识别算法里面进行人脸识别
            # 这里不一定是一张图片，如果需要的话你可以获取多张图片一起进行一次人脸识别（如果这样可以提高识别的准确率的话）
            result  = self.face_recognition(img)
            if result is False:
                # 如果没有检测到人的话
                pass
            else:
                # 如果检测到人的话
                name, number, health_code = result

        elif msg_topic == subTopic["get_temperature"]:
            """
            此时是测量完体温了，esp32把体温信息发送给我们
            """
            pass

    def rec_img(self, request):
        """
        获取esp32当前捕获的图片
        :param request: 用于获取指定esp32的图片
        :return: esp32当前捕获的图片
        """

        while True:
            if request.raw.readline() == b'\r\n' and request.raw.readline() == b'--123456789000000000000987654321\r\n':
                request.raw.readline()
                # 图片的字节流的长度
                length = request.raw.readline()[16:-2]
                request.raw.readline()
                # 在这之前都是类似于响应头，这些信息用处不大，除了那个长度，下面这个才是整个图片
                img_data = request.raw.read(int(length))

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
        :return: 识别的结果：姓名、学/工号、健康码情况（正常或者不正常）,如果图片中没有人脸或者人脸不在数据库中就返回False
        """
        pass


faceDetector = FaceDetector()
mqtt_client.on_message = faceDetector.on_message
mqtt_client.loop_forever()
