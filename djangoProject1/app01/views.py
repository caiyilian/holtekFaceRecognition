from django.shortcuts import HttpResponse
from django.http import StreamingHttpResponse
from django.http import JsonResponse
# Create your views here.
from app01.util.convertImg import convert_img
from app01.util.face import face, crop
import cv2
import json
import requests
import numpy as np
import os
from datetime import datetime

eqNameDict = {}
# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('lyy2.avi', fourcc, 30.0, (320, 240))
count = 0
img001 = None

img002 = None


def getImg(request):
    print("有人想获取图片")

    def down():
        # cap = cv2.VideoCapture(0)
        # while True:
        #     img = cv2.resize(cap.read()[1], (320, 240))
        #     # print(convert_img(img))
        #     bboxs = convert_img(img)
        #     if len(bboxs) == 0:
        #         yield bytes([201, 203, 0, 0, 0, 0, 0, 0, 0, 0])
        #         continue
        #     # print([201, 202] + sorted(bboxs, key=lambda x: x[4])[-1][:-1])
        #     yield bytes([201, 202] + sorted(bboxs, key=lambda x: x[4])[-1][:-1])
        full_url = request.get_full_path()
        eqName = full_url[full_url.rfind("=") + 1:]
        if eqName == '003':
            eqName = "002"
        print(eqNameDict[eqName])
        url = f"http://{eqNameDict[eqName]}:81/stream"
        res = requests.get(url, stream=True)
        while True:
            # print(res.raw.readline())
            # continue
            if res.raw.readline() == b'--123456789000000000000987654321\r\n':
                res.raw.readline()
                # 图片的字节流的长度
                length = res.raw.readline()[16:-2]
                res.raw.readline()
                # 在这之前都是类似于响应头，这些信息用处不大，除了那个长度，下面这个才是整个图片
                img = cv2.imdecode(np.frombuffer(res.raw.read(int(length)), dtype=np.uint8), cv2.IMREAD_COLOR)

                # print(img)
                # out.write(img)
                # global count
                # count += 1
                # if count == 300:
                #     out.release()
                #     exit()
                #     break
                # print(count)
                # continue
                cv2.imshow(eqName, img)
                cv2.waitKey(1)
                # 图片刷新率，每隔多少ms刷新一次图片
                img = cv2.resize(img, (320, 240))
                bboxs,crop_img = convert_img(img)

                if eqName == '001':
                    global img001
                    img001 = None if len(bboxs) == 0 else crop(img)
                else:
                    global img002
                    img002 = None if len(bboxs) == 0 else crop(img)
                if len(bboxs) == 0:
                    yield bytes([201, 203, 0, 0, 0, 0, 0, 0, 0, 0])
                    continue
                # print("有框")
                yield bytes([201, 202] + sorted(bboxs, key=lambda x: x[4])[-1][:-1])

    return StreamingHttpResponse(down())


def getResult(request):
    print("有人想要人脸识别")
    return HttpResponse("1")
    print("有人想要人脸识别")
    full_url = request.get_full_path()
    eqName = full_url[full_url.rfind("=") + 1:]
    if eqName == '003':
        eqName = "002"
    print(eqName)
    if eqName == "001":
        result = face(img001)
    else:
        result = face(img002)
    if result is None:
        print("没有人脸")
        return HttpResponse("1")

    else:
        cv2.imwrite("lyy.jpg", img001)
        # 如果检测到人的话

        # 下面就是把识别到的结果（姓名、号码）记录起来
        if os.path.exists(r"D:\cases\人脸识别模块\testing/" + eqName + ".json"):
            file = open(r"D:\cases\人脸识别模块\testing/" + eqName + ".json", "r", encoding="utf-8")
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
        if len(testing_record) != 0 and testing_record[-1].get("temperature") is None:
            testing_record[-1] = result
        else:
            testing_record.append(result)
        print("识别结果")
        print(result['name'])
        # 把添加后的列表重新写入json文件中
        with open(r"D:\cases\人脸识别模块\testing/" + eqName + ".json", "w", encoding="utf-8") as file:
            file.write(json.dumps(testing_record, indent=4, ensure_ascii=False))
        return HttpResponse("1")


def getIp(requests):
    full_url = requests.get_full_path()
    eqName = full_url[full_url.rfind("?") + 1:full_url.rfind("=")]
    if eqName == '003':
        eqName = "002"
    ip = full_url[full_url.rfind("=") + 1:]
    eqNameDict[eqName] = ip
    return HttpResponse("ok")


def getTemp(requests):
    full_url = requests.get_full_path()
    temperature = full_url[full_url.rfind("=") + 1:]
    eqName = full_url[full_url.find("=") + 1:full_url.find("&")]
    if eqName == '003':
        eqName = "002"
    print("温度：")
    print(temperature)
    print(eqName)
    # 这里直接读取文件，不错报错处理，因为实际过程中肯定是先人脸识别之后把姓名、号码、健康码状况写入文件后才进行体温测量，所以不可能不存在这个文件或者文件内容为空
    file = open(r"D:\cases\人脸识别模块\testing/" + eqName + ".json", "r", encoding="utf-8")
    testing_record = json.loads(file.read())

    if (38.5 > float(temperature) > 36) is False:
        # 如果温度过高，就要删除这条记录(也就是最后一条记录)，然后让这个同学去一旁留下观察
        testing_record.pop()

    else:
        # 遍历列表，找到还没有录入温度的那条记录，这个温度就是属于那一条记录的
        for index, each_record in enumerate(testing_record):
            if each_record.get("temperature") is None:
                break

        # 这里index飘黄，但是实际正常情况是一定能找到那个index所以如果真的报错就是逻辑有问题
        testing_record[index]["temperature"] = temperature
        testing_record[index]['time'] = datetime.now().strftime("%Y-%m-%d")
        testing_record[index]['result'] = "阴性"
    # 把添加/删除后的列表重新写入json文件中
    with open(r"D:\cases\人脸识别模块\testing/" + eqName + ".json", "w", encoding="utf-8") as file:
        file.write(json.dumps(testing_record, indent=4, ensure_ascii=False))
    return HttpResponse("ok")


def getRecord(request):
    recordLists = []
    for eqName in os.listdir(r"D:\cases\人脸识别模块\testing"):
        if eqName.endswith(".json"):
            with open(fr"D:\cases\人脸识别模块\testing/{eqName}", "r", encoding="utf-8") as file:
                recordLists += [obj for obj in json.loads(file.read()) if obj.get("temperature", None) is not None]

    return JsonResponse(data=recordLists, safe=False)
