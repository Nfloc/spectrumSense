#include <Wire.h>
#include <Adafruit_AS7341.h>

const as7341_color_channel_t channels[8] = {
  AS7341_CHANNEL_415nm_F1,
  AS7341_CHANNEL_445nm_F2,
  AS7341_CHANNEL_480nm_F3,
  AS7341_CHANNEL_515nm_F4,
  AS7341_CHANNEL_555nm_F5,
  AS7341_CHANNEL_590nm_F6,
  AS7341_CHANNEL_630nm_F7,
  AS7341_CHANNEL_680nm_F8
};

Adafruit_AS7341 as7341;

// Number of samples for dark-frame averaging
typedef uint16_t u16;
const int N_SAMPLES = 20;
u16 darkOffset[8];

// Prototype for dark-frame capture
void captureDarkFrame();

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  if (!as7341.begin()) {
    Serial.println("ERR_NO_SENSOR");
    while (1) delay(10);
  }

  // Configure sensor integration time and gain
  as7341.setASTEP(599);    // use default step size (optional)
  as7341.setATIME(60);     // ~100 ms total integration

  // Capture dark-frame offsets once at startup
  // captureDarkFrame();
  // Serial.println("Setup complete");
}

void loop() {
  // Re-capture dark frame on serial command 'D'
  if (Serial.available() && Serial.read() == 'D') {
    captureDarkFrame();
  }

  // Trigger a new 8-channel read
  if (!as7341.readAllChannels()) {
    Serial.println("Error reading channels!");
    delay(500);
    return;
  }
  // Loop through all 8 spectrometer channels, apply dark subtraction
  for (uint8_t ch = 0; ch < 8; ch++) {
    uint16_t raw = as7341.getChannel(channels[ch]);
    int16_t corrected = int16_t(raw) - int16_t(darkOffset[ch]);
    if (corrected < 0) corrected = 0;
    // Print as JSON object on one line
    Serial.printf("{\"ch\":%u,\"val\":%d}\n", ch, corrected);
    delay(50);
  }
  // Mark end of cycle
  Serial.println("{\"cycle\":true}");
}

void captureDarkFrame() {
  Serial.println("Capturing dark frame...");
  uint32_t sum[8] = {0};

  for (int i = 0; i < N_SAMPLES; i++) {
    delay(120);  // Wait integration time + margin
    for (uint8_t ch = 0; ch < 8; ch++) {
      sum[ch] += as7341.getChannel(channels[ch]);
    }
  }

  for (uint8_t ch = 0; ch < 8; ch++) {
    darkOffset[ch] = sum[ch] / N_SAMPLES;
    Serial.printf("Dark[ch%u]=%u\n", ch, darkOffset[ch]);
  }
  Serial.println("Dark frame captured.");
}

