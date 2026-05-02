// ------------------------------------------------------------
//   Trigger Box Controller
//   Version: v000
//   Target: Industrial Shields M-Duino 19R+
// ------------------------------------------------------------
// Operating modes:
//
// Mode = 1:
//   Constant / test spark mode.
//   If Arm is active, the spark output is pulsed repeatedly.
//
// Mode = 0:
//   Hydrogen test mode.
//   Sequence:
//     1. Wait for Arm
//     2. Wait for Trigger
//     3. Activate hot wires for BurnTime seconds
//     4. Fire spark
//     5. Send DAQ trigger pulse
//     6. Latch system as Fired to prevent repeated firing
//
// IMPORTANT:
//   This version only adds comments.
//   No executable logic has been intentionally changed.
// ------------------------------------------------------------


// ------------------------------------------------------------
// Output pin assignments
// ------------------------------------------------------------

// Arming indicator light
const int ArmLight = R0_5;

// Hot-wire outputs.
// These likely energise relays or outputs used to melt/cut the vent film.
const int HotWire1 = R0_6;
const int HotWire2 = R0_7;
const int HotWire3 = R0_8;


// ------------------------------------------------------------
// Input pin assignments
// ------------------------------------------------------------

// Trigger input.
// Used to initiate the hydrogen-test firing sequence when armed.
const int Trigger = I0_4;

// Mode selector input.
// Mode = 1 -> spark test mode.
// Mode = 0 -> hydrogen test mode.
const int Mode = I0_5;

// Arm input.
// The system can only fire when this input is active.
const int Arm = I0_3;


// ------------------------------------------------------------
// Output pin assignments for ignition and DAQ
// ------------------------------------------------------------

// Spark output.
// This likely drives the ignition/spark module.
const int SparkOut = Q0_1;

// DAQ trigger output.
// This is used to trigger the data acquisition system.
const int DAQTrig = Q0_0;


// ------------------------------------------------------------
// Global variables
// ------------------------------------------------------------

int active;

// Used in the firing loop.
// In the current code, the loop only runs once.
int times = 0;

// Spark output pulse duration in microseconds.
// dwell = 5000 means SparkOut is HIGH for 5 ms.
int dwell = 5000;

// Hot-wire activation time in seconds.
// BurnTime = 10 means the hot wires are ON for 10 seconds.
int BurnTime = 10;

// Delay between DAQ trigger activation and end of spark pulse,
// in microseconds.
// With dwell = 5000 and Delay = 600:
//   SparkOut is HIGH first for 4400 us.
//   DAQTrig is then HIGH for the last 600 us.
//   Then both outputs are set LOW.
int Delay = 600;

// Counter used in Melty() to create the BurnTime delay.
int count;


// ------------------------------------------------------------
// State flags
// ------------------------------------------------------------

// Used to prevent repeated execution of the firing block.
boolean flag = false;

// True when the system is logically armed.
boolean Armed = false;

// True if the trigger was pressed before the system was armed.
// This creates a fail/interlock condition.
boolean Fail = false;

// True after the firing sequence has been completed.
// Prevents repeated firing until reset.
boolean Fired = false;

// Enables or disables the hot-wire step.
// Current value true means the hot-wire sequence is always used.
//
// IMPORTANT:
// This variable is a boolean flag, not a pin number.
// However, later in setup() the code uses:
//   pinMode(HotWire, OUTPUT);
// That is suspicious because HotWire is true/false, not HotWire1/2/3.
boolean HotWire = true;


// ------------------------------------------------------------
// setup()
// Runs once when the controller starts
// ------------------------------------------------------------

void setup() {

  // Configure input pins
  pinMode(Trigger, INPUT);
  pinMode(Mode, INPUT);
  pinMode(Arm, INPUT);

  // WARNING:
  // This line configures "HotWire", which is a boolean flag,
  // not HotWire1, HotWire2, or HotWire3.
  //
  // Since HotWire = true, this may effectively configure pin 1,
  // depending on the Arduino/M-Duino environment.
  //
  // This is probably not what was intended.
  pinMode(HotWire, OUTPUT);

  // Configure ignition and DAQ outputs
  pinMode(SparkOut, OUTPUT);
  pinMode(DAQTrig, OUTPUT);

  // Configure arming light output
  pinMode(ArmLight, OUTPUT);

  // Start serial communication for debugging/status output
  Serial.begin(9600);
}


// ------------------------------------------------------------
// Melty()
// Activates the hot wires for BurnTime seconds
// ------------------------------------------------------------

void Melty() {

  // Turn all three hot-wire outputs ON
  digitalWrite(HotWire1, HIGH);
  digitalWrite(HotWire2, HIGH);
  digitalWrite(HotWire3, HIGH);

  // Keep the hot wires ON for BurnTime seconds.
  //
  // BurnTime = 10 means this loop waits:
  //   10 x 1000 ms = 10 seconds
  //
  // WARNING:
  // This is a blocking delay.
  // During this time, the controller does not check Arm,
  // Trigger, Mode, or any emergency/cancel logic.
  for(count = 0; count < BurnTime ; count++)
  {
    delay(1000);
  }

  // Turn all three hot-wire outputs OFF
  digitalWrite(HotWire1, LOW);
  digitalWrite(HotWire2, LOW);
  digitalWrite(HotWire3, LOW);
}


// ------------------------------------------------------------
// ConstSpark()
// Spark-test mode
// ------------------------------------------------------------
// This function is used when Mode == 1.
//
// If Arm is active:
//   - ArmLight is turned ON.
//   - SparkOut is pulsed HIGH for dwell microseconds.
//
// If Arm is not active:
//   - ArmLight is OFF.
//   - SparkOut is forced LOW.
// ------------------------------------------------------------

void ConstSpark(){

  if (digitalRead(Arm) == 1)    
  {
    // Indicate that the system is armed
    digitalWrite(ArmLight, HIGH);

    // Send one spark pulse
    digitalWrite(SparkOut, HIGH);
    delayMicroseconds(dwell);
    digitalWrite(SparkOut, LOW);
  }
  else
  {
    // If not armed, keep outputs safe/off
    digitalWrite(ArmLight, LOW);
    digitalWrite(SparkOut, LOW);
  }
}


// ------------------------------------------------------------
// HydrogenTest()
// Main hydrogen-test firing logic
// ------------------------------------------------------------
// Used when Mode == 0.
//
// Intended logic:
//   1. Reset if both Trigger and Arm are released.
//   2. Set Fail if Trigger is pressed before Arm.
//   3. Arm the system only if no Fail and not already Fired.
//   4. If Trigger is pressed while Armed, run the firing sequence.
//   5. After firing, latch Fired = true and disarm.
// ------------------------------------------------------------

void HydrogenTest(){

  // ----------------------------------------------------------
  // Reset condition
  // ----------------------------------------------------------
  // If both Trigger and Arm are released, reset the Fired and
  // Fail states.
  //
  // This means the operator must release both controls before
  // the system can be used again after firing or fail.
  if ((digitalRead(Trigger) == 0) && (digitalRead(Arm) == 0))
  {
    Fired = false;
    Fail = false;
  }

  // ----------------------------------------------------------
  // Fail condition
  // ----------------------------------------------------------
  // If Trigger is pressed while Arm is not active,
  // set Fail = true.
  //
  // This prevents firing if the trigger was pressed before
  // the system was properly armed.
  if ((digitalRead(Trigger) == 1) && (digitalRead(Arm) == 0))
  {
    Fail = true;
  }


  // ----------------------------------------------------------
  // Arming logic
  // ----------------------------------------------------------
  // The system becomes Armed only if:
  //   - Fail is false
  //   - Arm input is active
  //   - The system has not already fired
  //
  // If armed, the arm light is turned ON.
  // Otherwise, the system is disarmed and the arm light is OFF.
  if ((Fail == false) && (digitalRead(Arm) == 1)  && (Fired == false) /*&& (digitalRead(Trigger) != 1)*/)
  {
    Armed = true;
    digitalWrite(ArmLight,HIGH);
  }
  else 
  { 
    Armed = false;
    digitalWrite(ArmLight,LOW);
  }  


  // ----------------------------------------------------------
  // Firing condition
  // ----------------------------------------------------------
  // The firing sequence starts only when:
  //   - Trigger is active
  //   - Armed is true
  //   - Fired is false
  if ((digitalRead(Trigger) == 1) && (Armed == true) && (Fired == false))
  {
    // flag is used as an additional latch.
    // However, Fired already prevents repeated firing,
    // so flag may be partly redundant.
    if ((flag == false) && (Fired == false))
    {
      // This loop currently runs only once because:
      //   times = 0; times < 1; times++
      for(times = 0; times < 1; times++)
      {
        // If hot-wire mode is enabled, activate the hot wires.
        //
        // Since HotWire = true globally, this will normally run.
        // Melty() blocks for BurnTime seconds.
        if (HotWire == true)
        {
          Melty();
        }

        // ----------------------------------------------------
        // Spark and DAQ trigger timing
        // ----------------------------------------------------
        //
        // SparkOut goes HIGH first.
        digitalWrite(SparkOut, HIGH);

        // Wait for dwell - Delay microseconds.
        //
        // With dwell = 5000 and Delay = 600:
        //   delayMicroseconds(4400)
        delayMicroseconds(dwell-Delay);

        // DAQ trigger goes HIGH near the end of the spark pulse.
        digitalWrite(DAQTrig, HIGH);

        // DAQTrig remains HIGH for Delay microseconds.
        //
        // With Delay = 600:
        //   DAQTrig is HIGH for 600 us.
        delayMicroseconds(Delay);

        // End both the spark output and DAQ trigger output.
        digitalWrite(SparkOut, LOW);
        digitalWrite(DAQTrig, LOW);

        // Latch the system as fired.
        Fired = true;

        // Small blocking delay after firing.
        delay(100);
      }

      // Prevent this block from running again until reset.
      flag = true;
    }
  }

  else
  {
    // If firing condition is not active, keep DAQ trigger LOW.
    digitalWrite(DAQTrig, LOW);

    // Reset flag and disarm.
    //
    // Note:
    // This branch runs whenever the outer firing condition is false.
    flag = false;
    Armed = false;
  }


  // ----------------------------------------------------------
  // Post-firing safety state
  // ----------------------------------------------------------
  // Once Fired == true:
  //   - Disarm the system
  //   - Turn off the arm light
  //   - Force DAQ trigger LOW
  //
  // WARNING:
  // digitalWrite(HotWire, LOW) uses HotWire, which is a boolean,
  // not HotWire1/2/3.
  //
  // This probably does not turn off HotWire1, HotWire2, HotWire3.
  // In practice, Melty() already turns them off, but this line is
  // still suspicious.
  if ( Fired == true)
  {
    Armed = false;
    digitalWrite(ArmLight,LOW);
    digitalWrite(HotWire, LOW);
    digitalWrite(DAQTrig, LOW);
  }
}


/*
Previous or alternative input assignment.

const int Trigger = I0_3;
const int Mode = I0_4;
const int Arm = I0_5;

This suggests that the input wiring may have changed at some point.
The current active definitions are:
  Trigger = I0_4
  Mode    = I0_5
  Arm     = I0_3
*/


// ------------------------------------------------------------
// loop()
// Main repeated program loop
// ------------------------------------------------------------

void loop() {

  // Select operating mode.
  //
  // Mode = 1:
  //   Spark-test mode.
  //
  // Mode = 0:
  //   Hydrogen-test sequence.
  if (digitalRead(Mode) == 1){
    ConstSpark();
  }
  else{
    HydrogenTest();
  }


  // ----------------------------------------------------------
  // Serial debug output
  // ----------------------------------------------------------
  // Prints:
  //   Mode
  //   Arm
  //   Trigger
  //   tab
  //   Fired
  //   Fail
  //   Armed
  //   flag
  //
  // Example structure:
  //   Mode Arm Trigger    Fired Fail Armed flag
  //
  // Note:
  // The first three values are printed without separators,
  // so the output can be hard to read.
  Serial.print(digitalRead(Mode));
  Serial.print(digitalRead(Arm));
  Serial.print(digitalRead(Trigger));
  Serial.print('\t');
  Serial.print(Fired);
  Serial.print(Fail);
  Serial.print(Armed);
  Serial.println(flag);
}