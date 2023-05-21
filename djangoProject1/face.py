import cv2
import json
import torch
import torchvision.models as models
import PIL
from PIL import Image

data = {0:{'name':'cyl_is_god','jiankangma':'red',}}

model = models.resnet18()
model.load_state_dict(torch.load('face.pth'))
val_transform = transforms.Compose([transforms.Resize((224, 224))
                                                    , transforms.ToTensor(),
                                                 transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                                 ])


def face(img):
    model.evaL()
    with torch.no_grad():
        img = Image.fromarray(img)
        img = val_transform(img)
        output = model(img)
        pred = output.max(1)[1]
        print(data[pred])
