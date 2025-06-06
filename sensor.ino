#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>

// Configurações FIWARE
const char* SSID = "Wokwi-GUEST";
const char* PASSWORD = "";
const char* BROKER_MQTT = "20.55.28.240";
const int BROKER_PORT = 1883;
const char* ID_MQTT = "bpm_030";
const char* TOPICO_PUBLISH = "/TEF/bpm030/attrs";

WiFiClient espClient;
PubSubClient MQTT(espClient);

void conectarWiFi() {
  Serial.print("Conectando ao Wi-Fi ");
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void conectarMQTT() {
  while (!MQTT.connected()) {
    Serial.print("Conectando ao MQTT... ");
    if (MQTT.connect(ID_MQTT)) {
      Serial.println("conectado!");
    } else {
      Serial.print("falha, rc=");
      Serial.print(MQTT.state());
      Serial.println(" tentando novamente em 2 segundos");
      delay(2000);
    }
  }
}

#define pin_trig 4
#define pin_echo 16
#define led 14
#define buzz 32

void setup(){
  Serial.begin(115200);
  pinMode(pin_trig, OUTPUT);
  pinMode(pin_echo, INPUT);
  pinMode(led, OUTPUT);
  pinMode(buzz, OUTPUT);

  // Conecta Wi-Fi e MQTT
  conectarWiFi();
  MQTT.setServer(BROKER_MQTT, BROKER_PORT);
}

void loop(){
  digitalWrite(pin_trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pin_trig, LOW);

  int duration = pulseIn(pin_echo, HIGH);
  Serial.print("Distância da água em cm: ");
  int distance = duration / 58;
  Serial.println(distance);

  if (distance < 200){
    digitalWrite(led, HIGH);
    digitalWrite(led, LOW);
    digitalWrite(buzz, HIGH);
    digitalWrite(buzz, LOW);
  }
  else {
    digitalWrite(led, LOW);
    digitalWrite(buzz, LOW);
  }
  
  //MQTT
  if (!MQTT.connected()) {
    conectarMQTT();
  }
  MQTT.loop();

 

  String payload = "distance|" + String(distance);
  MQTT.publish("/TEF/distance002/attrs", payload.c_str());


  Serial.println("Dados enviados ao FIWARE:");
  Serial.println(payload);
  

  delay(1000);
}