#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include<stdint.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <PubSubClient.h>

#include<cstring>
// 测试HTTP请求用的URL
String URL = "";
bool isGetIp = false;
uint8_t zero_num = 0;
const char* mqttServer = "bemfa.com";
TFT_eSPI tft = TFT_eSPI(240, 320);
// 设置wifi接入信息(请根据您的WiFi信息进行修改)
const char* ssid = "Tomoya";
const char* password = "12345678";
int waitBytes = 0;



WiFiClient wifiClient;
//创建 HTTPClient 对象
HTTPClient httpClient;
WiFiClient wifiClient_rec;
PubSubClient mqttClient(wifiClient);
String eqName = "002";
byte receiveData;
void setup() {
  //初始化串口设置
  Serial.begin(115200);
pinMode(LED_BUILTIN, OUTPUT);
digitalWrite(LED_BUILTIN, HIGH);
  //设置ESP8266工作模式为无线终端模式
  WiFi.mode(WIFI_STA);

  //开始连接wifi
  WiFi.begin(ssid, password);

  //等待WiFi连接,连接成功打印IP
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    //    Serial.print(".");
  }
  //  Serial.println("");
  //  Serial.print("WiFi Connected!");

//  // 设置MQTT服务器和端口号
//  mqttClient.setServer(mqttServer, 9501);
//  //设置收到消息后的回调函数
//  mqttClient.setCallback(receiveCallback);
//  // 连接MQTT服务器
//  connectMQTTserver();
  tft.begin();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);
  //创建 WiFiClient 对象。该对象用于处理getStream函数所获取的服务器响应体




}

void loop() {
  if (1) {
    uint8_t img_buffer[30];

    size_t result = wifiClient_rec.readBytes(img_buffer, 30);
//    Serial.print("result=");
//    Serial.println(result);
    if (result == 0) {
      get_img();
    }
    for (uint8_t x = 0; 20 > x; x += 1) {
      
      if (img_buffer[x] == 201) {
        if(img_buffer[x + 1] == 202){
       tft.fillScreen(TFT_BLACK);
      tft.fillRect(img_buffer[x + 2] * 256 + img_buffer[x + 3], img_buffer[x + 4] * 256 + img_buffer[x + 5], img_buffer[x + 6] * 256 + img_buffer[x + 7], img_buffer[x + 8] * 256 + img_buffer[x + 9], 31);
      tft.fillRect(img_buffer[x + 2] * 256 + img_buffer[x + 3] + 1, img_buffer[x + 4] * 256 + img_buffer[x + 5] + 1, img_buffer[x + 6] * 256 + img_buffer[x + 7] - 2, img_buffer[x + 8] * 256 + img_buffer[x + 9] - 2, 0);
      break;
        }
        else if(img_buffer[x + 1] == 203){
          tft.fillScreen(TFT_BLACK);
          break;
          }
      }
     

    }




      while(Serial.available() > 0){
        if(Serial.read()==170){
          receiveData = Serial.read();
          if(receiveData==85){
              Serial.read();
              String temperature = String(float(Serial.read()+Serial.read()/10.0),1);
              send_temp(temperature);
            }
           else if(receiveData==2){
            digitalWrite(LED_BUILTIN, LOW);
            String face_result = get_face_result();
            Serial.print("face_result=");
            Serial.println(face_result);
            if(face_result=="1"){
              Serial.write(0x01);
              }
              else{
                Serial.write(0x00);
                }
            }
          }
        }
  }
}


void get_img() {
  
  Serial.println("进入了get_img函数");
  httpClient.end();
  httpClient.begin(wifiClient, "http://tomoya.vip3gz.91tunnel.com:80/getImg/?eqName=" + eqName);
  int httpCode = httpClient.GET();
  wifiClient_rec = httpClient.getStream();
}
String get_face_result(){
    httpClient.end(); // 清理资源占用
  httpClient.begin(wifiClient, "http://tomoya.vip3gz.91tunnel.com:80/getResult/?eqName=" + eqName);
  int httpCode = httpClient.GET();
  String responsePayload = "0";
  if (httpCode == HTTP_CODE_OK) {
    responsePayload = httpClient.getString();
  } 
  httpClient.end(); // 清理资源占用
  return responsePayload;
  }
  
  void send_temp(String sendStr){
//  HTTPClient httpClient1;
//  WiFiClient wifiClient1;
  Serial.println("进入了send_temp函数");
  httpClient.end();
  httpClient.begin(wifiClient, "http://tomoya.vip3gz.91tunnel.com:80/getTemp/?eqName="+eqName+"&temp=" + sendStr);
  //启动连接并发送HTTP请求
  int httpCode = httpClient.GET();

  
  //如果服务器响应OK则从服务器获取响应体信息并通过串口输出
  //如果服务器不响应OK则将服务器响应状态码通过串口输出
  if (httpCode == HTTP_CODE_OK) {
    String responsePayload = httpClient.getString();
//    Serial.println("Server Response Payload: ");
//    Serial.println(responsePayload);
  } else {
//    Serial.println("Server Respose Code：");
//    Serial.println(httpCode);
  }
  //关闭ESP8266与服务器连接
  httpClient.end();
    }
