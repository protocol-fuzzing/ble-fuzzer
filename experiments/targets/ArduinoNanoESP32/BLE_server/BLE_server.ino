#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

#define SERVICE_UUID        "00001523-1212-efde-1523-785feabcd123"
#define CHARACTERISTIC_UUID "00001524-1212-efde-1523-785feabcd123"

uint8_t lbs_button_val = 2;

class ServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        Serial.println("Device Connected!");
        pServer->getAdvertising()->stop();
    }

    void onDisconnect(BLEServer* pServer) {
        Serial.println("Device Disconnected!");
        pServer->getAdvertising()->start();
    }
};

void setup() {
  Serial.begin(9600);
  delay(2000);
  Serial.println("Starting BLE!");

  BLESecurity* pSecurity = new BLESecurity();
  pSecurity->setAuthenticationMode(ESP_LE_AUTH_NO_BOND);
  pSecurity->setCapability(ESP_IO_CAP_NONE);
  pSecurity->setInitEncryptionKey(ESP_BLE_ENC_KEY_MASK);
  pSecurity->setRespEncryptionKey(ESP_BLE_ENC_KEY_MASK);

  BLEDevice::init("Nano");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLECharacteristic *pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_READ);
  pCharacteristic->setAccessPermissions(ESP_GATT_PERM_READ_ENCRYPTED);
  pCharacteristic->setValue(&lbs_button_val, sizeof(lbs_button_val));
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("Started advertising!");
  Serial.println(pCharacteristic->getHandle());
}

void loop() {
  delay(2000);
  Serial.println("Ping");
}