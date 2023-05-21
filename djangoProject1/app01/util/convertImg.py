import cv2
import mediapipe as mp

mpFaceDetection = mp.solutions.face_detection  # 人脸识别
mpDraw = mp.solutions.drawing_utils
faceDetection = mpFaceDetection.FaceDetection(0.5)


def convert_img_50(img):
    result_50 = []
    for x in range(0, img.shape[0]):
        for y in range(0, img.shape[1]):
            r, g, b = img[x, y, :]
            color16 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

            result_50 += [color16 // 256, color16 % 256]
    return result_50


def convert_img(input_img):
    crop_img = None
    img = cv2.cvtColor(cv2.rotate(input_img, cv2.ROTATE_90_CLOCKWISE), cv2.COLOR_BGR2RGB)
    results = faceDetection.process(img)
    bboxs = []
    if results.detections:
        for id, detection in enumerate(results.detections):
            bboxC = detection.location_data.relative_bounding_box
            bbox = int(bboxC.xmin * img.shape[1]), int(bboxC.ymin * img.shape[0]), int(bboxC.width * img.shape[1]), int(
                bboxC.height * img.shape[0])
            bboxs.append([])
            for i in bbox:
                if 0 > i:
                    i = 0
                bboxs[-1].append(i // 256)
                bboxs[-1].append(i % 256)
            bboxs[-1].append(bbox[2] * bbox[3])
            # print("bbox")
            # print(img.shape)
            List = [
                bbox[0] if bbox[0]>=0 else 0,
                (bbox[0]+bbox[2]) if (bbox[0]+bbox[2]) >= 0 else 0,
                bbox[1] if bbox[1] >= 0 else 0,
                (bbox[1]+bbox[3]) if (bbox[1]+bbox[3]) >= 0 else 0,
            ]
            crop_img = input_img[List[0]:List[1], List[2]:List[3], :]
            cv2.rectangle(img, bbox, (255, 0, 255), 1)

    # cv2.imshow("img",img)
    cv2.waitKey(100)
    return bboxs, crop_img
    # return convert_img_50(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))


if __name__ == '__main__':
    img = cv2.resize(cv2.imread("witch.jpg"), (50, 50))  # Need to be sure to have a 8-bit input
    result = convert_img(img)
