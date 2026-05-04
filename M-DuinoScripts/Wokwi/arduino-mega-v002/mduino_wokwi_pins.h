#pragma once

/*
  Wokwi / Arduino Mega compatibility mapping for the
  Industrial Shields M-Duino v002 trigger-box firmware.

  This header only remaps the M-Duino symbolic pin names
  used by the production firmware onto ordinary Arduino Mega
  GPIO pins so the state machine can be simulated in Wokwi.

  IMPORTANT
    - This is only for logic/timing simulation.
    - It does not simulate the real M-Duino I/O electronics.
    - It does not simulate relay, hot-wire, or ignition hardware.
*/

// Relay / indicator outputs
#define R0_5 22  // armLightPin
#define R0_6 23  // hotWire1Pin
#define R0_7 24  // hotWire2Pin
#define R0_8 25  // hotWire3Pin

// Operator inputs
#define I0_4 26  // triggerInputPin
#define I0_5 27  // modeInputPin
#define I0_3 28  // armInputPin

// Output command lines
#define Q0_1 29  // sparkOutPin
#define Q0_0 30  // daqTrigPin
