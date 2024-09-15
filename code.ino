// 보드 : ESP32 DEV MODULE
// 파티션 : 2MB APP / 2MB SPIFFS

#include <WiFi.h>

WiFiServer server(2021);

const char *ssid = "juyoung";
const char *password = "87654321ab";

int left_dir = 0; // 0 : 전진 , 1 : 후진
int right_dir = 0; // 0 : 전진 , 1 : 후진
int left_power = 0;
int right_power = 0;
unsigned long power_send_millis;
unsigned long power_received_millis;
unsigned long ip_send_millis;

#define POWER_SEND_PERIOD 100
#define IP_SEND_PERIOD 1000

#include "esp_camera.h"
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

camera_fb_t * fb = NULL;

void setup()
{
  // 시리얼 통신시작
  Serial.begin(115200);
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);

  // 카메라 설정
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 25000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 10;
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_DRAM;

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi..");
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(500);
  }
  Serial.println("");
  // Print ESP32 Local IP Address
  Serial.println(WiFi.localIP());
  server.begin();

  digitalWrite(4, LOW);
  delay(100);
  digitalWrite(4, HIGH);
  delay(100);
  digitalWrite(4, LOW);
  delay(100);
  digitalWrite(4, HIGH);
  delay(100);
  ip_send_millis = millis();
}

void loop()
{
  if ( ( millis() - power_send_millis ) > POWER_SEND_PERIOD )
    // 일정시간 PC로붙터 신호를 받지 못한 경우 차량 정지
  {
    Serial.write(20);
    Serial.write(1);
    Serial.write(0);
    Serial.write(0);
    Serial.write(0);
    Serial.write(0);
    power_send_millis = millis();
  }

  if ( ( millis() - ip_send_millis ) > IP_SEND_PERIOD )
  // IP_SEND_PERIOD 주기로 차량에 IP를 전송
  {
    IPAddress ip = WiFi.localIP();
    Serial.write(20);
    Serial.write(2);
    Serial.write(ip[0]);
    Serial.write(ip[1]);
    Serial.write(ip[2]);
    Serial.write(ip[3]);
    ip_send_millis = millis();
  }

  digitalWrite(4, LOW);
  WiFiClient client = server.available();
  if (client)
  {
    digitalWrite(4, LOW);
    delay(100);
    digitalWrite(4, HIGH);
    delay(100);
    digitalWrite(4, LOW);
    delay(100);
    digitalWrite(4, HIGH);
    delay(100);

    //    Serial.println("New Client.");
    while (client.connected())
    {
      if ( ( millis() - power_received_millis ) > 1000 )
        // 일정시간 차선에 따른 모터 출력 값을 수신받지 못하면 모터 정지
      {
        left_power = 0;
        right_power = 0;
      }
      if ( ( millis() - power_send_millis ) > POWER_SEND_PERIOD )
      {
        Serial.write(20);
        Serial.write(1);
        Serial.write(left_dir);
        Serial.write(left_power);
        Serial.write(right_dir);
        Serial.write(right_power);
        power_send_millis = millis();
      }
      while ( client.available() >= 5 )
      {
        int val = client.read();
        if ( val == 20 )
        {
          left_dir = client.read();
          left_power = client.read();
          right_dir = client.read();
          right_power = client.read();
          power_received_millis = millis();
        }
      }
      //      Serial.print("SEND START - ");
      camera_fb_t *fb = NULL;
      esp_err_t res = ESP_OK;
      fb = esp_camera_fb_get();
      if (!fb)
      {
        //        Serial.println("Camera capture failed");
      }
      int length = fb->len;
      client.write(20);
      client.write(21);
      client.write((char*)&length, 2);
      //      Serial.print(length);
      client.write((char*)fb->buf, length);
      esp_camera_fb_return(fb);
      //      Serial.println(" - SEND END");
    }
  }
}
