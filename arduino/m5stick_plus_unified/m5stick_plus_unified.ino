#include <M5Unified.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- CONFIGURATION ---
#define SSID "Jl"
#define PASSWORD "turalBG789"
#define API_URL "http://172.20.10.9:8000/api/measures/"
#define DEVICE_TOKEN "f03e4d7e2d4592d39bdc5501a78d421cb01a8388"

// Pin Hardware pour le Grove Ear Clip sur M5StickC Plus 1.1
// Port Grove : Yellow=G32, White=G33
const int heartPin = 33; 

// --- VARIABLES RYTHME CARDIAQUE ---
volatile unsigned long lastBeatTime = 0;
volatile unsigned long beatInterval = 0;
volatile bool beatDetected = false;
volatile unsigned int totalBeats = 0; // Pour debug

float baseBPM = 0;
bool isCalibrated = false;
bool isCalibrating = false;
unsigned long calibrationStartTime = 0;
float calibrationBPMTotal = 0;
int calibrationReads = 0;

// --- VARIABLES TREMBLEMENTS ---
float shakeIntensity = 0;
float prevAccX = 0, prevAccY = 0, prevAccZ = 0;

// --- DIVERS ---
uint32_t tsLastReport = 0;

// Fonction d'interruption (ISR) pour le pouls
void IRAM_ATTR heartBeatISR() {
    unsigned long currentTime = millis();
    unsigned long interval = currentTime - lastBeatTime;
    if (interval > 300) { // Max 200 BPM
        beatInterval = interval;
        lastBeatTime = currentTime;
        beatDetected = true;
        totalBeats++;
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n--- POLYGRAPH UNIFIED START ---");

    auto cfg = M5.config();
    M5.begin(cfg);
    
    M5.Display.setRotation(3);
    M5.Display.fillScreen(BLACK);
    M5.Display.setCursor(0, 0, 2);
    M5.Display.println("POLYGRAPH UNIFIED");

    Serial.println("[INIT] IMU & Heart sensor...");
    // Init Capteur Cardiaque (GPIO 32)
    // On force l'arrêt de l'I2C sur ce pin et on active la résistance interne
    pinMode(heartPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(heartPin), heartBeatISR, FALLING);
    // WiFi
    Serial.printf("[WIFI] Connexion a %s...\n", SSID);
    WiFi.begin(SSID, PASSWORD);
    M5.Display.print("WiFi...");
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
        delay(500);
        M5.Display.print(".");
        Serial.print(".");
        retry++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WIFI] OK! IP: " + WiFi.localIP().toString());
        M5.Display.println("\nWiFi OK!");
    } else {
        Serial.println("\n[WIFI] Echec de connexion (Time out)");
        M5.Display.println("\nWiFi Error!");
    }
    delay(1000);

    M5.Display.fillScreen(BLACK);
    M5.Display.println("Pret.");
    M5.Display.println("Bouton M: Calibrer");
    M5.Display.println("Bouton Cote: Reset");

    // Auto-enregistrement au boot
    Serial.println("[API] Envoi du Ping d'enregistrement...");
    sendUnifiedData(0, 0);
}

void loop() {
    M5.update(); // Gère les boutons et l'état interne
    
    // --- BOUTON RESET (Côté) ---
    if (M5.BtnB.wasPressed()) {
        Serial.println("[SYS] Reset demande par bouton.");
        M5.Display.fillScreen(RED);
        M5.Display.setCursor(10, 50, 4);
        M5.Display.println("REBOOT...");
        delay(1000);
        ESP.restart();
    }

    // --- LOGIQUE RYTHME CARDIAQUE ---
    static float currentBPM = 0; // 'static' indispensable pour conserver la valeur
    bool newBeatCalculated = false; // Marqueur pour la calibration

    if (beatDetected) {
        noInterrupts();
        unsigned long interval = beatInterval;
        beatDetected = false;
        interrupts();
        if (interval > 0) {
            currentBPM = 60000.0 / (float)interval;
            newBeatCalculated = true; // On signale un nouveau relevé
        }
    }

    // --- LOGIQUE TREMBLEMENTS (IMU) ---
    float ax, ay, az;
    M5.Imu.getAccel(&ax, &ay, &az);
    float delta = abs(ax - prevAccX) + abs(ay - prevAccY) + abs(az - prevAccZ);
    shakeIntensity = (shakeIntensity * 0.8) + (delta * 0.2); 
    prevAccX = ax; prevAccY = ay; prevAccZ = az;

    // --- GESTION CALIBRATION (Bouton Principal) ---
    if (M5.BtnA.wasPressed() && !isCalibrating) {
        Serial.println("[BTN] Bouton A Presse - Debut Calibration");
        isCalibrating = true;
        isCalibrated = false;
        calibrationStartTime = millis();
        calibrationBPMTotal = 0;
        calibrationReads = 0;
    }

    if (isCalibrating) {
        // On enregistre uniquement sur un NOUVEAU battement
        if (newBeatCalculated && currentBPM > 40 && currentBPM < 200) {
            calibrationBPMTotal += currentBPM;
            calibrationReads++;
            Serial.printf("[CALIB] Nouveau releve : %.1f BPM\n", currentBPM);
        }
        
        if (millis() - calibrationStartTime > 10000) { // 10 secondes
            isCalibrating = false;
            if (calibrationReads > 0) {
                baseBPM = calibrationBPMTotal / calibrationReads;
                isCalibrated = true;
                Serial.printf("[CALIB] TERMINE ! Base BPM : %.1f\n", baseBPM);
            } else {
                Serial.println("[CALIB] ECHEC : Aucun battement valide detecte en 10s.");
            }
        }
    }

    // --- AFFICHAGE ÉCRAN ---
    if (millis() % 200 < 20) {
        M5.Display.setCursor(0, 0, 2);
        if (isCalibrating) {
            M5.Display.fillScreen(BLUE);
            M5.Display.println("CALIBRATION...");
            M5.Display.printf("Lectures: %d\n", calibrationReads);
        } else {
            M5.Display.fillScreen(BLACK);
            M5.Display.printf("BPM: %.1f (B:%.0f)\n", currentBPM > 0 ? currentBPM : 0, baseBPM);
            M5.Display.printf("Tremblement: %.2f\n", shakeIntensity);
            
            // Barre visuelle
            int barW = map(shakeIntensity * 100, 0, 100, 0, M5.Display.width());
            M5.Display.fillRect(0, 100, barW, 20, shakeIntensity > 0.5 ? RED : GREEN);
            
            if (totalBeats > 0 && millis() % 1000 < 50) {
                Serial.printf("[DEBUG] Battements detectes total : %d\n", totalBeats);
            }
            
            if (isCalibrated) M5.Display.println("\n[SYNC API: OK]");
            else M5.Display.println("\n[ATTENTE CALIB.]");
        }
    }

    // --- ENVOI API (Toutes les 500ms si calibré) ---
    if (isCalibrated && (millis() - tsLastReport > 500)) {
        if (WiFi.status() == WL_CONNECTED) {
            sendUnifiedData(currentBPM > 0 ? currentBPM : 0, shakeIntensity);
        }
        tsLastReport = millis();
    }

    delay(20);
}

void sendUnifiedData(float bpm, float shake) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[ERR] WiFi deconnecte, abandon de l'envoi.");
        return;
    }

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Token " DEVICE_TOKEN);

    StaticJsonDocument<256> doc;
    doc["device_mac"] = WiFi.macAddress();
    doc["bpm"] = bpm;
    doc["base_bpm"] = baseBPM;
    doc["shake_intensity"] = shake;

    String body;
    serializeJson(doc, body);
    
    Serial.print("[API] Envoi: ");
    Serial.println(body);

    int httpResponseCode = http.POST(body);
    
    if (httpResponseCode > 0) {
        Serial.printf("[API] Succes (HTTP %d)\n", httpResponseCode);
        String response = http.getString();
        Serial.println("[API] Reponse: " + response);
    } else {
        Serial.printf("[API] Erreur d'envoi (HTTP ERROR %d): %s\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
    }
    http.end();
}