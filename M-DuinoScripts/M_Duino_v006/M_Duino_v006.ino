/*
  ============================================================
  Trigger Box Controller
  Version: v006
  Target: Industrial Shields M-Duino 19R+
  ============================================================

  PURPOSE
    This controller manages a test sequence with the following order:

      1. Operator arms the system
      2. Operator presses Trigger
      3. Hot-wire relays energize for a defined time
      4. SparkOut turns ON and the coil dwell interval begins
      5. DAQ trigger turns ON near the end of the dwell interval
      6. Outputs turn OFF
      7. The physical ignition spark is expected at or immediately after
         the SparkOut falling edge when the coil field collapses
      8. System stays locked out until both Arm and Trigger are released

  OPERATING MODES
    Mode HIGH:
      Spark-test mode

    Mode LOW:
      Hydrogen-test mode

  ELECTRICAL NOTES
    - The M-Duino outputs only command relays / drivers.
    - The hot-wire power comes from an external power source.
    - Example system:
        Hot-wire supply: 12 VDC
        Hot-wire current: up to 20 A
    - This controller must NOT carry that current directly.

  SAFETY NOTES
    - This software is NOT a substitute for a hardwired emergency stop.
    - The emergency stop should physically remove power from:
        * the hot-wire supply
        * the spark / ignition system

  DEBUGGING NOTES
    - This version keeps the structured state machine, but the actual
      SparkOut dwell timing is executed as a blocking, print-free section
      so coil timing stays close to the configured microsecond values.
    - Serial debug is disabled by default in this production-oriented
      version because even modest UART blocking can badly distort a
      5 ms dwell window.
    - In spark-test mode, repeating SparkOut dwell cycles run only while
      both Arm and Trigger remain active.
    - Releasing either Arm or Trigger stops spark-test activity immediately.
    - The state machine makes debugging easier because the controller
      always has one clear "current state".
    - Open the Serial Monitor at 9600 baud to see:
        * startup configuration
        * state transitions
        * periodic status lines
    - For safe bench testing, use the real controller hardware with:
        * the M-Duino powered normally
        * the Mac connected by USB for upload / serial monitoring
        * the hot-wire power and spark hardware disconnected

  UNITS
    - All timing variables use microseconds.
    - Any variable ending in "_us" is in microseconds.
    - Pins, booleans, and states do not have physical units,
      so they do not get a unit suffix.
*/


// ============================================================
// Pin assignments
// ============================================================

// Output: panel light showing that the system is armed
const int armLightPin = R0_5;

// Outputs: relay control lines for the three hot wires
const int hotWire1Pin = R0_6;
const int hotWire2Pin = R0_7;
const int hotWire3Pin = R0_8;

// Inputs
const int triggerInputPin = I0_4;
const int modeInputPin = I0_5;
const int armInputPin = I0_3;

// Outputs
const int sparkOutPin = Q0_1;
const int daqTrigPin = Q0_0;


// ============================================================
// Hardware logic configuration
// ============================================================

// Set to false if your digital inputs are electrically active LOW.
const bool inputActiveHigh = true;

// Set to false if your outputs / relay modules are electrically active LOW.
const bool outputActiveHigh = true;

// For Industrial Shields hardware, INPUT is usually correct.
// If your hardware requires pull-ups, use INPUT_PULLUP and also
// set inputActiveHigh = false.
const int inputMode = INPUT;


// ============================================================
// Feature configuration
// ============================================================

// If false, the hydrogen test skips the hot-wire stage
// and goes directly to the spark stage.
const bool useHotWireStep = true;

// Enable serial status output for monitoring and debugging.
const bool enableSerialDebug = false;

// Enable detailed messages when the controller changes state.
const bool enableTransitionDebug = false;

// Exact firmware file intended to be running on the controller.
const char* firmwareScriptName = "M_Duino_v006.ino";


// ============================================================
// Timing configuration
// All values below are in microseconds
// ============================================================

const unsigned long usPerMs = 1000UL;
const unsigned long usPerS = 1000000UL;

// Hot-wire ON duration before SparkOut dwell starts.
// Production example: 20 seconds = 20,000,000 us
const unsigned long hotWireBurn_us = 20UL * usPerS;

// Total SparkOut dwell / ignition-command duration.
// Production example: 5000 us = 5 ms
const unsigned long sparkDwell_us = 5000UL;

// DAQ trigger pulse width.
// DAQ will be active during the final daqPulse_us of the dwell interval.
// Production example: 600 us = 0.6 ms
const unsigned long daqPulse_us = 600UL;

// In spark-test mode, the next SparkOut dwell cycle starts at this interval
// while spark-test is enabled.
// Production example: 500,000 us = 0.5 s
const unsigned long sparkTestInterval_us = 500UL * usPerMs;

// Debounce time for mechanical input switches.
// A new raw input level must remain unchanged for this full interval
// before the firmware accepts it as the new stable state.
// Production example: 30,000 us = 30 ms
//
// Practical meaning:
//   - This can add up to about 30 ms of input acceptance delay.
//   - That delay is intentional and helps reject switch bounce.
//   - It does not mean the whole controller is delayed by 30 ms;
//     it only affects recognition of a changed input state.
const unsigned long debounce_us = 30UL * usPerMs;

// Serial debug print interval.
// Production example: 250,000 us = 0.25 s
const unsigned long serialPrintInterval_us = 250UL * usPerMs;


// ============================================================
// Debounced input helper
// ============================================================

/*
  DebouncedInput stores:
    - the pin number
    - the current stable logical state
    - the last raw logical state
    - the time of the last raw change in microseconds

  Logic convention:
    active() == true means the input is logically active,
    independent of whether the hardware is active HIGH or LOW.

  Debounce behavior:
    - If the raw input changes, a debounce timer effectively restarts.
    - The new state is accepted only after the raw level has remained
      unchanged for the full debounce_us interval.
    - This is a common and robust software debounce method for
      mechanical switches.
*/
struct DebouncedInput {
  int pin;
  bool stableState;
  bool lastRawState;
  unsigned long lastRawChange_us;

  void begin(int inputPin) {
    pin = inputPin;
    pinMode(pin, inputMode);

    bool rawState = readRawActive();
    stableState = rawState;
    lastRawState = rawState;
    lastRawChange_us = micros();
  }

  bool readRawActive() const {
    bool pinIsHigh = (digitalRead(pin) == HIGH);
    return inputActiveHigh ? pinIsHigh : !pinIsHigh;
  }

  void update() {
    bool rawState = readRawActive();
    unsigned long now_us = micros();

    // Any raw change restarts the debounce interval.
    if (rawState != lastRawState) {
      lastRawState = rawState;
      lastRawChange_us = now_us;
    }

    // Accept the new state only after it has remained stable for the
    // full debounce interval.
    if ((now_us - lastRawChange_us) >= debounce_us) {
      stableState = rawState;
    }
  }

  bool active() const {
    return stableState;
  }
};

DebouncedInput triggerInput;
DebouncedInput modeInput;
DebouncedInput armInput;


// ============================================================
// State machine
// ============================================================

/*
  stateIdle
    Safe resting state. Waiting for a clean start.

  stateArmed
    Arm is active. Waiting for Trigger.

  stateMelting
    Hot-wire relays are energized.

  stateSparkWaitDaq
    Name retained for sequence terminology. In v006, the actual dwell
    timing is executed in one blocking timing section rather than by
    repeated loop polling.

  stateSparkWaitEnd
    Name retained for sequence terminology. In v006, this stage is not
    stretched by debug printing because the SparkOut/DAQ timing window
    runs print-free inside one blocking helper.

  stateFired
    Sequence completed successfully. Lockout until inputs are released.

  stateFail
    Invalid operator action, such as Trigger active before proper arming.

  stateAborted
    Sequence interrupted because Arm was released during a hazardous phase.
*/
enum SystemState {
  stateIdle,
  stateArmed,
  stateMelting,
  stateSparkWaitDaq,
  stateSparkWaitEnd,
  stateFired,
  stateFail,
  stateAborted
};

SystemState currentState = stateIdle;


// ============================================================
// Runtime timing variables
// All timing values below are in microseconds
// ============================================================

// Timestamp when the hot-wire stage started
unsigned long meltStart_us = 0;

// Timestamp when the SparkOut dwell stage started
unsigned long sparkStart_us = 0;

// Timestamp of the most recent serial debug print
unsigned long lastSerialPrint_us = 0;

// Spark-test mode timing variables
bool sparkTestEnabled = false;
bool sparkTestPulseActive = false;
unsigned long sparkTestStart_us = 0;
unsigned long lastSparkTestPulse_us = 0;

// Used to detect changes between spark-test mode and hydrogen-test mode
bool previousSparkTestMode = false;


// ============================================================
// Debug helper declarations
// ============================================================

const char* stateName(SystemState state);
void changeState(SystemState newState, const char* reason);
void printStartupConfiguration();


// ============================================================
// Output helper functions
// ============================================================

/*
  writeOutput(pin, on)
    Converts logical ON/OFF into the actual electrical level
    required by the hardware.

  If outputActiveHigh = true:
    on  -> HIGH
    off -> LOW

  If outputActiveHigh = false:
    on  -> LOW
    off -> HIGH
*/
void writeOutput(int pin, bool on) {
  bool pinShouldBeHigh = outputActiveHigh ? on : !on;
  digitalWrite(pin, pinShouldBeHigh ? HIGH : LOW);
}

void setArmLight(bool on) {
  writeOutput(armLightPin, on);
}

void setSpark(bool on) {
  writeOutput(sparkOutPin, on);
}

void setDaqTrigger(bool on) {
  writeOutput(daqTrigPin, on);
}

void setHotWires(bool on) {
  writeOutput(hotWire1Pin, on);
  writeOutput(hotWire2Pin, on);
  writeOutput(hotWire3Pin, on);
}

/*
  allOutputsOff()
    Safe output state used:
      - at startup
      - on failure
      - on abort
      - after the sequence finishes
      - during mode changes
*/
void allOutputsOff() {
  setArmLight(false);
  setHotWires(false);
  setSpark(false);
  setDaqTrigger(false);
}


// ============================================================
// State helper functions
// ============================================================

/*
  daqStartDelay_us()

  Example with current settings:
    sparkDwell_us = 5000 us
    daqPulse_us   = 600 us

  Sequence:
    SparkOut ON at t = 0 us (coil dwell begins)
    DAQ ON      at t = 4400 us
    SparkOut OFF and DAQ OFF at t = 5000 us
    Physical ignition spark expected at or immediately after the
    SparkOut falling edge
*/
unsigned long daqStartDelay_us() {
  if (sparkDwell_us > daqPulse_us) {
    return sparkDwell_us - daqPulse_us;
  }
  return 0;
}

/*
  Trigger is a maintained/latching operator input.
  Arm must remain active during hazardous phases.
*/
bool armStillActive() {
  return armInput.active();
}

/*
  enterSafeLockout(newState)
    Forces all outputs OFF and enters a lockout state.
    Lockout states require both Arm and Trigger to be released
    before returning to stateIdle.
*/
void enterSafeLockout(SystemState newState, const char* reason) {
  allOutputsOff();
  changeState(newState, reason);
}

/*
  delayMicrosecondsLong(duration_us)
    Executes a microsecond delay in chunks so the code does not rely on
    a 16-bit cast if the configured interval is ever increased beyond
    65,535 us.
*/
void delayMicrosecondsLong(unsigned long duration_us) {
  const unsigned int maxChunk_us = 65000U;

  while (duration_us > maxChunk_us) {
    delayMicroseconds(maxChunk_us);
    duration_us -= maxChunk_us;
  }

  if (duration_us > 0) {
    delayMicroseconds((unsigned int)duration_us);
  }
}

/*
  runSparkDwellBlocking(enableDaq)
    Executes the ignition-command dwell as one blocking, print-free timing
    section so serial/debug activity cannot stretch the coil dwell.

    Tradeoff:
      - timing accuracy is much better than v005
      - however, Arm is not re-polled during this very short blocking
        dwell window itself
*/
void runSparkDwellBlocking(bool enableDaq) {
  setSpark(true);

  if (!enableDaq) {
    delayMicrosecondsLong(sparkDwell_us);
    setSpark(false);
    return;
  }

  unsigned long daqDelay_us = daqStartDelay_us();

  if (daqDelay_us > 0) {
    delayMicrosecondsLong(daqDelay_us);
  }

  setDaqTrigger(true);

  if (sparkDwell_us > daqDelay_us) {
    delayMicrosecondsLong(sparkDwell_us - daqDelay_us);
  }

  setSpark(false);
  setDaqTrigger(false);
}

/*
  runHydrogenSparkSequenceBlocking()
    Hot wires are forced OFF, then the SparkOut dwell/DAQ phase is executed
    without any serial logging or loop-level timing jitter in between.
*/
void runHydrogenSparkSequenceBlocking() {
  setHotWires(false);
  setDaqTrigger(false);
  currentState = stateSparkWaitDaq;
  sparkStart_us = micros();
  runSparkDwellBlocking(true);
  allOutputsOff();
  changeState(stateFired, "spark dwell completed");
}

/*
  startMeltingOrSpark()
    If hot-wire stage is enabled:
    start MELTING
    Otherwise:
      jump directly to SPARK
*/
void startMeltingOrSpark() {
  if (useHotWireStep) {
    setArmLight(true);
    setHotWires(true);
    setSpark(false);
    setDaqTrigger(false);

    meltStart_us = micros();
    changeState(stateMelting, "trigger pressed while armed");
  } else {
    runHydrogenSparkSequenceBlocking();
  }
}


// ============================================================
// Setup
// ============================================================

void setup() {
  // Initialize debounced inputs
  triggerInput.begin(triggerInputPin);
  modeInput.begin(modeInputPin);
  armInput.begin(armInputPin);

  // Configure outputs
  pinMode(armLightPin, OUTPUT);
  pinMode(hotWire1Pin, OUTPUT);
  pinMode(hotWire2Pin, OUTPUT);
  pinMode(hotWire3Pin, OUTPUT);
  pinMode(sparkOutPin, OUTPUT);
  pinMode(daqTrigPin, OUTPUT);

  // Force a known safe startup state
  allOutputsOff();

  Serial.begin(9600);

  // Store the initial mode so startup is not mistaken for a mode change
  previousSparkTestMode = modeInput.active();

  printStartupConfiguration();
}


// ============================================================
// Input update
// ============================================================

void updateInputs() {
  triggerInput.update();
  modeInput.update();
  armInput.update();
}


// ============================================================
// Spark-test mode
// ============================================================

/*
  Spark-test mode behavior:
    - Hot wires always OFF
    - DAQ always OFF
    - If Arm is inactive:
        all outputs are OFF and spark-test is disabled
    - If Trigger is inactive:
        all outputs are OFF and spark-test is disabled
    - Spark-test runs only while both Arm and Trigger remain active
*/
void handleSparkTestMode() {
  setHotWires(false);
  setDaqTrigger(false);

  unsigned long now_us = micros();
  bool triggerActive = triggerInput.active();

  if (!armInput.active()) {
    allOutputsOff();
    sparkTestEnabled = false;
    sparkTestPulseActive = false;
    return;
  }

  if (!triggerActive) {
    allOutputsOff();
    sparkTestEnabled = false;
    sparkTestPulseActive = false;
    return;
  }

  if (!sparkTestEnabled) {
    sparkTestEnabled = true;

    // Allow the first pulse to start immediately after enabling.
    lastSparkTestPulse_us = now_us - sparkTestInterval_us;

    if (enableTransitionDebug) {
      Serial.println("SPARK_TEST_EVENT: Spark-test enabled by maintained Trigger");
    }
  }

  setArmLight(true);

  if (!sparkTestPulseActive && ((now_us - lastSparkTestPulse_us) >= sparkTestInterval_us)) {
    sparkTestStart_us = now_us;
    lastSparkTestPulse_us = now_us;
    sparkTestPulseActive = true;

    if (enableTransitionDebug) {
      Serial.println("SPARK_TEST_EVENT: SparkOut dwell cycle started");
    }

    runSparkDwellBlocking(false);
    sparkTestPulseActive = false;

    if (enableTransitionDebug) {
      Serial.println("SPARK_TEST_EVENT: SparkOut dwell cycle ended");
    }
  }
}


// ============================================================
// Hydrogen-test mode
// ============================================================

/*
  Hydrogen-test sequence summary:

    stateIdle
      -> wait for Trigger released and Arm activation

    stateArmed
      -> wait for Trigger press

    stateMelting
      -> hot-wire relays ON for hotWireBurn_us

    stateSparkWaitDaq
      -> internal blocking dwell/DAQ phase

    stateSparkWaitEnd
      -> retained as a named state for sequence terminology

    stateFired
      -> all outputs OFF, wait for full operator reset

  Unsafe / invalid conditions:

    stateFail
      Trigger was active before valid arming

    stateAborted
      Arm was released during MELTING or SPARK
*/
void handleHydrogenTestMode() {
  bool armActive = armInput.active();
  bool triggerActive = triggerInput.active();

  switch (currentState) {

    case stateIdle:
      allOutputsOff();

      // Trigger must not already be active before arming
      if (triggerActive) {
        changeState(stateFail, "trigger active before valid arming");
      } else if (armActive) {
        setArmLight(true);
        changeState(stateArmed, "arm input became active");
      }
      break;

    case stateArmed:
      setArmLight(true);
      setHotWires(false);
      setSpark(false);
      setDaqTrigger(false);

      if (!armActive) {
        changeState(stateIdle, "arm released before trigger");
      } else if (triggerActive) {
        startMeltingOrSpark();
      }
      break;

    case stateMelting:
      setArmLight(true);
      setHotWires(true);
      setSpark(false);
      setDaqTrigger(false);

      // Arm must remain active during melting
      if (!armStillActive()) {
        enterSafeLockout(stateAborted, "arm released during melting");
        break;
      }

      if ((micros() - meltStart_us) >= hotWireBurn_us) {
        setHotWires(false);
        runHydrogenSparkSequenceBlocking();
      }
      break;

    case stateSparkWaitDaq:
    case stateSparkWaitEnd:
      allOutputsOff();
      changeState(stateFired, "blocking spark sequence completed");
      break;

    case stateFired:
      allOutputsOff();

      // Require both inputs released before allowing re-arm
      if (!armActive && !triggerActive) {
        changeState(stateIdle, "operator reset after fired state");
      }
      break;

    case stateFail:
      allOutputsOff();

      // Require both inputs released before allowing re-arm
      if (!armActive && !triggerActive) {
        changeState(stateIdle, "operator reset after fail state");
      }
      break;

    case stateAborted:
      allOutputsOff();

      // Require both inputs released before allowing re-arm
      if (!armActive && !triggerActive) {
        changeState(stateIdle, "operator reset after aborted state");
      }
      break;
  }
}


// ============================================================
// Mode change handling
// ============================================================

/*
  If the operator changes Mode during operation,
  immediately return to a safe state.

  This avoids carrying sequence state from one mode into the other.
*/
void handleModeChange() {
  bool sparkTestMode = modeInput.active();

  if (sparkTestMode != previousSparkTestMode) {
    allOutputsOff();

    sparkTestEnabled = false;
    sparkTestPulseActive = false;

    changeState(stateIdle, sparkTestMode ? "mode changed to spark-test" : "mode changed to hydrogen-test");

    previousSparkTestMode = sparkTestMode;
  }
}


// ============================================================
// Serial debug output
// ============================================================

const char* stateName(SystemState state) {
  switch (state) {
    case stateIdle: return "IDLE";
    case stateArmed: return "ARMED";
    case stateMelting: return "MELTING";
    case stateSparkWaitDaq: return "SPARK_WAIT_DAQ";
    case stateSparkWaitEnd: return "SPARK_WAIT_END";
    case stateFired: return "FIRED";
    case stateFail: return "FAIL";
    case stateAborted: return "ABORTED";
    default: return "UNKNOWN";
  }
}

/*
  changeState(newState, reason)

  All state transitions go through this helper so the Serial Monitor
  shows the sequence in real time.

  Example output:
    STATE: ARMED -> MELTING | reason=trigger pressed while armed
*/
void changeState(SystemState newState, const char* reason) {
  if (newState == currentState) {
    return;
  }

  if (enableSerialDebug && enableTransitionDebug) {
    Serial.print("STATE: ");
    Serial.print(stateName(currentState));
    Serial.print(" -> ");
    Serial.print(stateName(newState));

    if (reason != 0) {
      Serial.print(" | reason=");
      Serial.print(reason);
    }

    Serial.println();
  }

  currentState = newState;
}

/*
  Print startup configuration so the operator can immediately confirm:
    - mode logic polarity assumptions
    - relay polarity assumptions
    - current timing values
    - the exact timing values in use
*/
void printStartupConfiguration() {
  if (!enableSerialDebug) {
    return;
  }

  Serial.println("================================================");
  Serial.println("Trigger Box Controller v006 startup");
  Serial.print("Firmware script: ");
  Serial.println(firmwareScriptName);
  Serial.print("Input active HIGH: ");
  Serial.println(inputActiveHigh);
  Serial.print("Output active HIGH: ");
  Serial.println(outputActiveHigh);
  Serial.print("Hot-wire step enabled: ");
  Serial.println(useHotWireStep);
  Serial.print("hotWireBurn_us: ");
  Serial.println(hotWireBurn_us);
  Serial.print("sparkDwell_us: ");
  Serial.println(sparkDwell_us);
  Serial.print("daqPulse_us: ");
  Serial.println(daqPulse_us);
  Serial.print("sparkTestInterval_us: ");
  Serial.println(sparkTestInterval_us);
  Serial.println("Open Serial Monitor at 9600 baud for live sequence logs.");
  Serial.println("================================================");
}

/*
  Print a compact status line at a limited rate
  so the serial monitor remains readable.
*/
void printStatusThrottled() {
  if (!enableSerialDebug) {
    return;
  }

  unsigned long now_us = micros();

  if ((now_us - lastSerialPrint_us) < serialPrintInterval_us) {
    return;
  }

  lastSerialPrint_us = now_us;

  Serial.print("STATUS | Mode=");
  Serial.print(modeInput.active() ? "SPARK_TEST" : "HYDROGEN_TEST");

  Serial.print(" | Arm=");
  Serial.print(armInput.active());

  Serial.print(" | Trigger=");
  Serial.print(triggerInput.active());

  Serial.print(" | State=");
  Serial.print(stateName(currentState));

  Serial.print(" | HotWireStep=");
  Serial.print(useHotWireStep);

  Serial.print(" | hotWireBurn_us=");
  Serial.print(hotWireBurn_us);

  Serial.print(" | sparkDwell_us=");
  Serial.print(sparkDwell_us);

  Serial.print(" | daqPulse_us=");
  Serial.print(daqPulse_us);

  Serial.println();
}


// ============================================================
// Main loop
// ============================================================

void loop() {
  updateInputs();
  handleModeChange();

  if (modeInput.active()) {
    handleSparkTestMode();
  } else {
    handleHydrogenTestMode();
  }

  printStatusThrottled();
}
