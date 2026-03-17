#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define SSID "Jl"
#define PASSWORD "turalBG789"
#define API_URL "http://172.20.10.9:8000/api/measures/"
// Token Django du compte Arduino (récupéré depuis /api/users/login/ ou l'admin)
#define DEVICE_TOKEN "f03e4d7e2d4592d39bdc5501a78d421cb01a8388"

// Configuration matérielle pour le Adafruit HUZZAH32 ESP32 Feather
const int heartPin = 15;      // Pin où est connecté le Grove Ear Clip

// Variables partagées avec l'interruption
volatile unsigned long lastBeatTime = 0;
volatile unsigned long beatInterval = 0;
volatile bool beatDetected = false;

// Variables globales de calibration et d'état
float baseBPM = 0;
bool isCalibrated = false;
bool isCalibrating = false;
unsigned long calibrationStartTime = 0;
float calibrationBPMTotal = 0;
int calibrationReads = 0;
uint32_t tsLastReport = 0;

// -- Pas de bouton externe utilisé --

// Fonction d'interruption (ISR) appelée à chaque battement détecté par le capteur
void IRAM_ATTR heartBeatISR() {
    unsigned long currentTime = millis();
    unsigned long interval = currentTime - lastBeatTime;
    
    // On ignore les "rebonds" ou bruits < 300ms (ce qui correspond à max 200 BPM)
    if (interval > 300) {
        beatInterval = interval;
        lastBeatTime = currentTime;
        beatDetected = true;
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("--- Demarrage du Detecteur de Mensonges (HUZZAH32) ---");

    // Initialisation WiFi
    WiFi.begin(SSID, PASSWORD);
    Serial.print("Connexion WiFi...");
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WiFi OK! IP: " + WiFi.localIP().toString());
    } else {
        Serial.println("Echec WiFi... Continuera hors-ligne.");
    }
    delay(1000);

    // Initialisation du capteur Grove Ear Clip
    pinMode(heartPin, INPUT);
    attachInterrupt(digitalPinToInterrupt(heartPin), heartBeatISR, RISING);
    
    Serial.println("Capteur Grove Cardiaque initialise sur la Pin " + String(heartPin));
    delay(1000);
    
    Serial.println("==================================================");
    Serial.println("Envoyez 'c' dans le Serial");
    Serial.println("pour lancer la calibration de base (10 secondes).");
    Serial.println("==================================================");
}

void loop() {
    // Calcul du BPM actuel basé sur l'interruption
    float currentBPM = 0;
    if (beatDetected) {
        noInterrupts();
        unsigned long interval = beatInterval;
        beatDetected = false;
        interrupts();
        
        if (interval > 0) {
             currentBPM = 60000.0 / (float)interval;
        }
    }

    // Gestion du lancement de la calibration
    bool serialPressed = (Serial.available() > 0 && Serial.read() == 'c');

    if (serialPressed && !isCalibrating) {
        isCalibrating = true;
        isCalibrated = false;
        calibrationStartTime = millis();
        calibrationBPMTotal = 0;
        calibrationReads = 0;
        tsLastReport = millis();
        
        Serial.println("\n>>> DEBUT DE LA CALIBRATION (Restez calme) ...");
    }

    // --- PHASE DE CALIBRATION (10 secondes) ---
    if (isCalibrating) {
        if (currentBPM > 40 && currentBPM < 200) {  
            calibrationBPMTotal += currentBPM;
            calibrationReads++;
            Serial.printf("BPM lu : %.1f\n", currentBPM);
        }

        if (millis() - calibrationStartTime > 10000) {
            isCalibrating = false;

            if (calibrationReads > 0) {
                baseBPM = calibrationBPMTotal / calibrationReads;
                isCalibrated = true;
                Serial.printf("\n>>> CALIBRATION TERMINEE. BPM de base : %.1f\n", baseBPM);
                Serial.println(">>> DEMARRAGE DU TEST DE MENSONGE...");
            } else {
                Serial.println("\n>>> ERREUR CALIBRATION : Aucun pouls dectecte. Veuillez recommencer.");
            }
        }
    } 
    // --- PHASE OPERATIONNELLE ---
    else if (isCalibrated) {
        // Envoi toutes les 500ms s'il y a un pouls
        if (currentBPM > 40 && millis() - tsLastReport > 500) { 
            Serial.printf("[INFO] Pulsation detectee. (BPM: %.1f, Base: %.1f)\n", currentBPM, baseBPM);

            if (WiFi.status() == WL_CONNECTED) {
                sendData(currentBPM);
            } else {
                Serial.println("  (Non envoye, WiFi deconnecte)");
            }
            
            tsLastReport = millis();
        }
    }
}

void sendData(float bpm) {
    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Token " DEVICE_TOKEN);

    StaticJsonDocument<200> doc;
    // L'adresse MAC sert d'identifiant unique pour l'appareil sur Django
    doc["device_mac"] = WiFi.macAddress();
    doc["bpm"] = bpm;
    doc["base_bpm"] = baseBPM;
    // Note: is_lie est dorenavant calcule cote API

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);
    
    if (httpResponseCode > 0) {
        Serial.printf("  -> Donnees envoyees au serveur (HTTP %d)\n", httpResponseCode);
    } else {
        Serial.printf("  -> Erreur d'envoi API (HTTP %d)\n", httpResponseCode);
    }
    http.end();
}
