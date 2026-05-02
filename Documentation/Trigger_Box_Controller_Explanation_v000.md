# Trigger Box Controller

Code review summary of the reviewed M-Duino control logic for operator understanding, peer review, and lab handover.

## 1. Purpose

This controller manages a trigger box with two operating modes:

- `Spark-test mode`
- `Hydrogen-test mode`

In hydrogen-test mode, the controller enforces a defined sequence:

1. The operator arms the system.
2. The operator presses `Trigger`.
3. The three hot-wire relay outputs turn on for a fixed time.
4. The spark output turns on.
5. The DAQ trigger turns on near the end of the spark pulse.
6. All outputs turn off.
7. The system remains locked out until both `Arm` and `Trigger` are released.

The revised code is longer than the original because it makes the sequence explicit and easier to audit. Instead of relying on several interacting flags, it uses a named state machine.

## 2. Hardware Signals

| Signal | Type | Purpose | Meaning in the logic |
|---|---|---|---|
| `Arm` | Digital input | Both modes | Allows the system to arm. Must remain active during hazardous phases. |
| `Trigger` | Digital input | Hydrogen-test mode | Starts the firing sequence after arming. Treated as a momentary start command. |
| `Mode` | Digital input | Both modes | Selects `Spark-test` or `Hydrogen-test` behavior. |
| `ArmLight` | Digital output | Both modes | Indicates that the system is armed or in an active sequence. |
| `HotWire1`, `HotWire2`, `HotWire3` | Digital outputs | Hydrogen-test mode | Drive the three relay channels that control the external hot-wire power system. |
| `SparkOut` | Digital output | Both modes | Commands the spark or ignition stage. |
| `DAQTrig` | Digital output | Hydrogen-test mode | Sends a timing pulse to the data-acquisition system. |

## 3. Unit Convention

The code uses explicit units where they matter.

- Any variable ending in `_us` is in `microseconds`.
- Pins, booleans, and states do not have physical units, so they do not get a unit suffix.

Examples:

- `hotWireBurn_us`
- `sparkDwell_us`
- `daqPulse_us`
- `sparkTestInterval_us`
- `debounce_us`
- `lastSerialPrint_us`
- `meltStart_us`
- `sparkStart_us`

This naming style makes the timing easier to understand and reduces mistakes when adjusting values.

## 4. Main Timing Variables

| Variable | Current value | Unit | Meaning |
|---|---|---|---|
| `hotWireBurn_us` | `10,000,000` | microseconds | Keeps the three hot-wire relay outputs on for 10 seconds. |
| `sparkDwell_us` | `5,000` | microseconds | Total spark pulse duration. |
| `daqPulse_us` | `600` | microseconds | Width of the DAQ trigger pulse at the end of the spark pulse. |
| `sparkTestInterval_us` | `500,000` | microseconds | Time between spark pulses in spark-test mode. |
| `debounce_us` | `30,000` | microseconds | Stable input time required before accepting a switch change. |
| `serialPrintInterval_us` | `250,000` | microseconds | Limits how often the serial monitor is updated. |

## 5. Sequence Overview

![Trigger box sequence diagram](/Users/javiercamacho/Desktop/Industrial PhD/Conference-Webinar-Workshops/2025/ICHS-INTERNATIONAL CONFERENCE ON HYDROGEN SAFETY  /10-Material-Books-Standards/SetUp-Design/SyncronisationBox/trigger_box_sequence_diagram_v002.png)

Figure 1. Trigger box sequence overview.

### Hydrogen-test mode

1. The controller starts in `stateIdle` with all outputs off.
2. If `Trigger` is already active before proper arming, the controller enters `stateFail`.
3. When `Arm` becomes active, the controller enters `stateArmed`.
4. When `Trigger` is pressed, the controller starts the hot-wire stage if `useHotWireStep = true`.
5. In `stateMelting`, all three hot-wire relay outputs stay on for `hotWireBurn_us`.
6. After that delay, the hot-wire outputs turn off and the spark pulse begins.
7. In `stateSparkWaitDaq`, `SparkOut` is on and `DAQTrig` is still off.
8. After `sparkDwell_us - daqPulse_us`, the controller turns `DAQTrig` on.
9. At the end of `sparkDwell_us`, the controller turns both `SparkOut` and `DAQTrig` off.
10. The controller enters `stateFired`.
11. The system remains locked out until both `Arm` and `Trigger` are released.

### Spark-test mode

- The hot-wire outputs stay off.
- The DAQ output stays off.
- If `Arm` is active, the controller generates periodic spark pulses.
- If `Arm` is released, the controller turns the spark output off immediately.

## 6. State Machine

The reviewed version uses a state machine instead of several loosely connected flags.

| State | Meaning |
|---|---|
| `stateIdle` | Safe waiting state with all outputs off. |
| `stateArmed` | Arm is active and the controller is waiting for Trigger. |
| `stateMelting` | The three hot-wire relay outputs are energized. |
| `stateSparkWaitDaq` | Spark is on and the controller is waiting for the DAQ start point. |
| `stateSparkWaitEnd` | Spark and DAQ are on and the controller is waiting for the end of the spark dwell time. |
| `stateFired` | The sequence completed successfully. Reset is required before a new cycle. |
| `stateFail` | An invalid start condition occurred, such as Trigger being active before proper arming. |
| `stateAborted` | The sequence was interrupted because Arm was released during a hazardous phase. |

## 7. Why This Version Is Safer and Easier to Read

Compared with the original short sketch, the reviewed version improves several important points:

- The hot-wire relay outputs are clearly separated from boolean flags.
- Timing variables include units in their names.
- The main sequence is explicit and easier to follow.
- Lockout behavior is deliberate rather than accidental.
- Unsafe transitions such as releasing `Arm` during the hot-wire or spark phase are handled immediately.
- Mode changes force the controller back to a safe state.

## 8. Code Structure

| Function or block | Role |
|---|---|
| `setup()` | Configures inputs and outputs, starts serial communication, and forces a safe startup state. |
| `loop()` | Updates inputs, checks for mode changes, runs the appropriate mode handler, and prints status. |
| `DebouncedInput` | Filters switch bounce so mechanical inputs behave more reliably. |
| `handleSparkTestMode()` | Runs spark-only behavior with a defined interval. |
| `handleHydrogenTestMode()` | Runs the main sequence and lockout logic. |
| `startMeltingOrSpark()` | Chooses whether to start the hot-wire stage or jump directly to spark. |
| `startSparkSequence()` | Forces hot wires off, starts the spark stage, and begins spark timing. |
| `allOutputsOff()` | Provides a reusable safe-off command for all outputs. |

## 9. Safety Behaviors Built Into the Logic

- All outputs are forced off at startup.
- All outputs are forced off after firing, failure, abort, or mode change.
- The controller requires `Arm` to remain active during the melting and spark phases.
- The controller requires both `Arm` and `Trigger` to be released before re-arming after a lockout state.
- The hot-wire outputs are turned off before the spark stage begins.

Important note:

- This software is not a substitute for a hardwired emergency stop.
- The emergency stop should physically remove power from the hot-wire supply and the spark system.

## 10. Hardware Points to Confirm

Before using the controller on the real setup, two hardware questions should be confirmed:

1. `Relay polarity`
   Some relay modules are active `LOW` rather than active `HIGH`. If the relays energize when the controller output goes low, the output logic in the code must be inverted.

2. `Input wiring`
   The `Arm`, `Trigger`, and `Mode` inputs must be electrically well-defined. If the wiring allows the input to float, the controller can behave unpredictably.

## 11. Practical Test Strategy

Recommended step-by-step validation:

1. Power the M-Duino correctly from its intended external supply.
2. Connect the Mac by USB only for upload and serial monitoring.
3. Test the logic first with the hazardous power stages disconnected.
4. Use the serial monitor to check `Mode`, `Arm`, `Trigger`, and the current state name.
5. Verify relay polarity on each hot-wire channel before connecting the real hot-wire power circuit.
6. Introduce the real hot-wire and spark hardware only after the low-risk logic checks pass.

## 12. Short Summary

This reviewed version keeps the same overall purpose as the original sketch, but it is easier to understand, easier to explain, and easier to review with colleagues. The main improvements are:

- clearer naming
- explicit timing units
- a proper state machine
- deliberate safety and lockout behavior
- a cleaner explanation of how hot wires, spark, and DAQ interact
