import time
import cv2
import numpy as np
import mediapipe as mp
import os

mpFaceDetection = mp.solutions.face_detection  # 人脸识别
mpDraw = mp.solutions.drawing_utils
mp_face_detection = mpFaceDetection.FaceDetection(0.5)
img_mean = [0.485, 0.456, 0.406]
img_std = [0.229, 0.224, 0.225]
data = {0: {'name': '蔡依炼', 'number': '2020001', 'healthCode': '正常', },
        1: {'name': '杨英杰', 'number': '2020002', 'healthCode': '正常', },
        2: {'name': '刘懿逸', 'number': '2020003', 'healthCode': '正常', },
        3: {'name': '蓬鹏', 'number': '2020004', 'healthCode': '正常', }, }
# /app01/util
predictor = cv2.dnn.readNetFromONNX('./app01/util/face_4_6.onnx')
# temppath = "./app01/util/temp"
# temps = {}
# for i in os.listdir(temppath):
#     t = cv2.imread(os.path.join(temppath , i))
#     t = cv2.resize(t, (50, 50))
#     temps[i.split('.')[0]] = t


def softmax(x):
    exp_x = np.exp(x)
    sum_exp_x = np.sum(exp_x)
    y = exp_x / sum_exp_x

    return y


def face(img):
    if img is None:
        return None
    img = cv2.resize(img, (224, 224))
    img = img.transpose(2, 0, 1) / 255.0
    img = (img - np.array(img_mean).reshape(
        (3, 1, 1))) / np.array(img_std).reshape((3, 1, 1))
    img = img.reshape([1, 3, 224, 224]).astype('float32')
    predictor.setInput(img)
    output = predictor.forward()
    output = softmax(output)
    print(output)
    pred = output[0].argmax() if output[0].max() > 0.5 else None
    # print(pred)
    try:
        info = data[int(pred)]
    except:
        info = None
    return info


def crop(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face_detection.process(frame)

    # 如果检测到了人脸
    if results.detections:
        # 遍历所有人脸检测结果
        for detection in results.detections:
            # 获取人脸在图像中的坐标信息
            x, y, w, h = int(detection.location_data.relative_bounding_box.xmin * frame.shape[1]), \
                         int(detection.location_data.relative_bounding_box.ymin * frame.shape[0]), \
                         int(detection.location_data.relative_bounding_box.width * frame.shape[1]), \
                         int(detection.location_data.relative_bounding_box.height * frame.shape[0])

            # 将人脸区域扣下来保存到文件
            face_region = frame[y:y + h, x:x + w]

            try:
                face_region = cv2.cvtColor(face_region, cv2.COLOR_RGB2BGR)
                return face_region
            except:
                return None


def match(image):
    image =  cv2.resize(image,(50,50))
    score = {}
    for name, temp in temps.items():
        result = cv2.matchTemplate(image, temp, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # print(name, max_val)
        score[name] = max_val
    return max(score, key=score.get)


if __name__ == '__main__':
    # img = cv2.imread("lyy.jpg")
    #
    # print(face(img))
    # exit()

    cam = cv2.VideoCapture('../../videos/pp.avi')
    while 1:
        ret, input_img = cam.read()
        img = crop(input_img)
        if img is not None:
            result = face(img)
            print(result)
            # print(face(img))
            cv2.imshow("img", img)
            cv2.waitKey(1)

        # print(img)
