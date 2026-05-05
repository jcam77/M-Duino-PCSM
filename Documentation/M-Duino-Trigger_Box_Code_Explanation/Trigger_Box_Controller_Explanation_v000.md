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
4. The ignition command output turns on and the coil dwell interval begins.
5. The DAQ trigger turns on near the end of the dwell interval.
6. All outputs turn off.
7. If the ignition system fires on coil collapse, the physical spark is released when the dwell signal goes low.
8. The system remains locked out until both `Arm` and `Trigger` are released.

The revised code is longer than the original because it makes the sequence explicit and easier to audit. Instead of relying on several interacting flags, it uses a named state machine.

## 2. Firmware Source Referenced

This explanation refers to the following source files in the repository:

- `M-DuinoScripts/M_Duino_v006/M_Duino_v006.ino`
- `M-DuinoScripts/M-Duino_Original/M-Duino_Original.ino`

Interpretation rule:

- the `.ino` files are the source of truth for the actual firmware logic
- this document explains the logic and terminology, but does not replace the source code itself

## 3. Hardware Signals

| Signal                                   | Type            | Purpose            | Meaning in the logic                                                            |
| ---------------------------------------- | --------------- | ------------------ | ------------------------------------------------------------------------------- |
| `Arm`                                  | Digital input   | Both modes         | Allows the system to arm. Must remain active during hazardous phases.           |
| `Trigger`                              | Digital input   | Hydrogen-test mode | Starts the firing sequence after arming. On the real box this may be a maintained switch rather than a momentary pushbutton. In hydrogen-test mode it must be returned to the inactive position before the next clean re-arm.  |
| `Mode`                                 | Digital input   | Both modes         | Selects `Spark-test` or `Hydrogen-test` behavior.                           |
| `ArmLight`                             | Digital output  | Both modes         | Indicates that the system is armed or in an active sequence. In hydrogen-test mode, the light staying off while `Trigger` remains active after a fired/fail/abort condition is intentional feedback that a clean reset has not yet been completed. In spark-test mode, the light turns on only while both `Arm` and `Trigger` are active.                    |
| `HotWire1`, `HotWire2`, `HotWire3` | Digital outputs | Hydrogen-test mode | Drive the three relay channels that control the external hot-wire power system. |
| `SparkOut`                             | Digital output  | Both modes         | Commands the ignition stage. In a coil-based setup, this typically defines the dwell / coil-charge interval rather than the exact physical spark duration. |
| `DAQTrig`                              | Digital output  | Hydrogen-test mode | Sends a timing pulse to the data-acquisition system.                            |

## 4. Unit Convention

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

### Why the reviewed script is better than the original on units

The reviewed `M_Duino_v006.ino` is better than the original sketch in how it handles units.

The original code used shorter names such as:

- `dwell`
- `Delay`

Those names are compact, but they are much easier to misunderstand because the unit and physical meaning are not visible at the point of use.

The reviewed code is clearer because names such as:

- `sparkDwell_us`
- `daqPulse_us`
- `hotWireBurn_us`

make the time unit explicit.

This improves:

- code readability
- auditability
- discussion with colleagues
- safety when changing timing values

Important nuance:

- `M_Duino_v006.ino` is clearly better on unit clarity
- but a few names still need physical interpretation in the documentation
- the main example is `sparkDwell_us`, which should be understood as coil dwell / ignition-command time, not literal plasma duration at the spark plug

## 5. Main Timing Variables

| Variable                   | Current value  | Unit         | Meaning                                                       |
| -------------------------- | -------------- | ------------ | ------------------------------------------------------------- |
| `hotWireBurn_us`         | `20,000,000` | microseconds | Keeps the three hot-wire relay outputs on for 20 seconds.     |
| `sparkDwell_us`          | `5,000`      | microseconds | Coil dwell / ignition-command duration before release. In a coil-based system, the physical spark is typically produced when this command goes low. |
| `daqPulse_us`            | `600`        | microseconds | Width of the DAQ trigger pulse during the final part of the dwell interval. |
| `sparkTestInterval_us`   | `500,000`    | microseconds | Time between ignition-command cycles in spark-test mode. |
| `debounce_us`            | `30,000`     | microseconds | Stable input time required before accepting a switch change. This can introduce up to about `30 ms` of input acceptance delay for a changed switch state. |
| `serialPrintInterval_us` | `250,000`    | microseconds | Limits how often the serial monitor is updated.               |

### Debounce interpretation

The debounce setting is often misunderstood, so it is useful to state it explicitly:

- `debounce_us = 30,000` means the firmware waits for the raw input to remain unchanged for about `30 ms` before accepting the new state.
- This can introduce up to about `30 ms` of input acceptance delay after a switch changes.
- That delay is intentional. It helps reject mechanical switch bounce and short noise spikes.
- It does **not** mean the whole controller is delayed by `30 ms` all the time. It only affects recognition of a changed input state.

The software method used here is:

- if the raw input changes, the debounce timer effectively restarts
- only when the raw level stays unchanged for the full debounce interval does the firmware update the accepted stable state

This is a common and robust debounce approach for mechanical operator controls such as `Arm`, `Trigger`, and `Mode`.

### Recommended feature settings for real hazardous tests

For a real hydrogen ignition run, the recommended feature configuration is:

- `useHotWireStep = true`
- `enableSerialDebug = false`
- `enableTransitionDebug = false`

Interpretation:

- `useHotWireStep = true` should remain enabled if the real experiment includes the hot-wire stage before ignition.
- `enableSerialDebug = false` is recommended for real firing because serial printing at `9600` baud can interfere with short timing windows such as `sparkDwell_us = 5000` and `daqPulse_us = 600`.
- `enableTransitionDebug = false` should also be disabled for the same reason.

The main `M_Duino_v006.ino` file now uses one fixed timing set for clarity. If shorter timings are needed for simulator visibility, that should be handled in a clearly separate Wokwi-specific file rather than through a runtime timing flag in the production firmware.

### Why `v005` was dangerous and how `v006` fixes it

The most important technical correction between `v005` and `v006` concerns the ignition dwell path.

In `v005`, serial debug output was still tied to state transitions inside the spark dwell sequence. At `9600` baud, each transmitted character takes about `1.04 ms`, and once the UART transmit buffer fills, `Serial.print()` blocks the CPU until enough bytes are sent. That is large enough to completely distort a `5 ms` ignition-command window.

The practical consequence was:

- `SparkOut` could be turned on
- serial transition text could then block the CPU during the dwell window
- `DAQTrig` and `SparkOut` turn-off timing could occur far later than intended

This was confirmed by direct oscilloscope measurement: the nominal `5 ms` dwell in `v005` stretched into the `>100 ms` range on the real hardware. That is dangerous for an ignition coil because it can overheat the primary winding and destroy the coil.

`v006` fixes this by moving the actual dwell timing into a single blocking, print-free function:

- `runSparkDwellBlocking()`

In `v006`, the SparkOut / DAQ timing window is executed without any serial printing or loop-level timing jitter in between. State logging happens only before or after the hardware has returned to a safe state.

Important nuance:

- `v006` removes the serial-induced over-dwell problem that was present in `v005`
- `v006` does **not** mean every possible ignition risk is eliminated
- it does mean the specific `v005` timing bug caused by debug output in the dwell path has been removed

One remaining implementation note in `v006` was also handled carefully:

- the dwell helper now delays in chunks so it does not rely on a silent 16-bit truncation if a future dwell value is ever increased beyond `65,535 us`

### DAQ output path note

The `DAQTrig` pulse is intentionally short. In the reviewed configuration it is only `600 us`, so the real DAQ trigger path should be verified as a **fast electronic output path**, not a mechanical relay path.

The practical hardware check is:

- confirm that the DAQ trigger is driven from the intended `Q` output path
- confirm that the signal is not later routed through a slow relay or bouncing contact
- confirm on an oscilloscope that the real pulse width and edge timing are acceptable at the DAQ input

## 6. Sequence Overview

![Trigger box sequence diagram](../Diagrams/trigger_box_sequence_diagram_v004.png)

Figure 1. Trigger box sequence overview.

Important interpretation note:

- The controller diagram is correct at the `SparkOut` command level.
- In a coil-based ignition system, the physical spark event is typically associated with the falling edge of `SparkOut`, not the moment `SparkOut` first goes high.
- This means the diagram should be read as a controller-sequence diagram, not as a literal plasma-duration diagram.

### Hydrogen-test mode

1. The controller starts in `stateIdle` with all outputs off.
2. If `Trigger` is already active before proper arming, the controller enters `stateFail`.
3. When `Arm` becomes active, the controller enters `stateArmed`.
4. When `Trigger` is pressed, the controller starts the hot-wire stage if `useHotWireStep = true`.
5. In `stateMelting`, all three hot-wire relay outputs stay on for `hotWireBurn_us`.
6. After that delay, the hot-wire outputs turn off and the ignition command stage begins.
7. In `v006`, the actual ignition dwell is executed inside one blocking, print-free helper rather than by loop polling through multiple serial-logged states.
8. In a coil-based system, this interval is the coil dwell / coil-charge interval.
9. After `sparkDwell_us - daqPulse_us`, the controller turns `DAQTrig` on.
10. At the end of `sparkDwell_us`, the controller turns both `SparkOut` and `DAQTrig` off.
11. If the ignition system fires on coil collapse, the physical spark is released at or immediately after this falling edge.
12. The controller enters `stateFired`.
13. The system remains locked out until both `Arm` and `Trigger` are released.

### Operator reset behavior

If the real `Trigger` control is a maintained switch rather than a momentary pushbutton, the reset/re-arm sequence is intentionally strict:

- after a fired, failed, or aborted cycle, both `Arm` and `Trigger` must be returned to the inactive position
- if `Trigger` remains active, the controller will not return to a clean ready state
- the `ArmLight` remaining off in that condition is intentional feedback to the operator

So in practical operator terms, the next hydrogen-test cycle should follow this sequence:

1. `Arm OFF`
2. `Trigger OFF`
3. `Arm ON`
4. `Trigger ON` to start the next run

### Spark-test mode

- The hot-wire outputs stay off.
- The DAQ output stays off.
- Spark-test runs only while both `Arm` and `Trigger` remain active.
- If `Trigger` is switched off, all spark-test outputs turn off immediately.
- If `Arm` is released, all spark-test outputs also turn off immediately.
- In spark-test mode, `ArmLight` does not follow `Arm` alone. It is on only while the maintained `Trigger` is also active.

## 7. State Machine

The reviewed version uses a state machine instead of several loosely connected flags.

| State                 | Meaning                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------- |
| `stateIdle`         | Safe waiting state with all outputs off.                                                |
| `stateArmed`        | Arm is active and the controller is waiting for Trigger.                                |
| `stateMelting`      | The three hot-wire relay outputs are energized.                                         |
| `stateSparkWaitDaq` | State name retained for sequence terminology. In `v006`, the actual dwell timing is executed inside one blocking helper so debug output cannot stretch the timing window. |
| `stateSparkWaitEnd` | State name retained for sequence terminology. In `v006`, this does not represent a serial-logged loop wait with outputs still active. |
| `stateFired`        | The sequence completed successfully. Reset is required before a new cycle.              |
| `stateFail`         | An invalid start condition occurred, such as Trigger being active before proper arming. |
| `stateAborted`      | The sequence was interrupted because Arm was released during a hazardous phase.         |

## 8. Why This Version Is Safer and Easier to Read

Compared with the original short sketch, the reviewed version improves several important points:

- The hot-wire relay outputs are clearly separated from boolean flags.
- Timing variables include units in their names.
- The main sequence is explicit and easier to follow.
- Lockout behavior is deliberate rather than accidental.
- Unsafe transitions such as releasing `Arm` during the hot-wire phase are handled immediately, and the dwell path itself is kept short and deterministic.
- Spark-test now matches the maintained trigger hardware more naturally.
- Mode changes force the controller back to a safe state.
- The `v005` serial-induced over-dwell problem is removed by executing the ignition dwell as a print-free blocking section.

## 9. Code Structure

| Function or block            | Role                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| `setup()`                  | Configures inputs and outputs, starts serial communication, and forces a safe startup state.   |
| `loop()`                   | Updates inputs, checks for mode changes, runs the appropriate mode handler, and prints status. |
| `DebouncedInput`           | Filters switch bounce so mechanical inputs behave more reliably.                               |
| `handleSparkTestMode()`    | Runs maintained-switch spark-test behavior, repeating ignition-command pulses only while both `Arm` and `Trigger` are active. |
| `handleHydrogenTestMode()` | Runs the main sequence and lockout logic.                                                      |
| `startMeltingOrSpark()`    | Chooses whether to start the hot-wire stage or jump directly to the ignition-command stage.                         |
| `delayMicrosecondsLong()`  | Executes microsecond delays in safe chunks so future longer dwell values do not silently truncate. |
| `runSparkDwellBlocking()`  | Executes the actual SparkOut / DAQ timing window without serial prints or loop-level timing jitter. |
| `runHydrogenSparkSequenceBlocking()` | Starts the blocking ignition-command section and only reports the completed state after outputs are safe. |
| `allOutputsOff()`          | Provides a reusable safe-off command for all outputs.                                          |

## 10. Safety Behaviors Built Into the Logic

- All outputs are forced off at startup.
- All outputs are forced off after firing, failure, abort, or mode change.
- The controller requires `Arm` to remain active during the melting and spark phases.
- The controller requires both `Arm` and `Trigger` to be released before re-arming after a lockout state.
- The hot-wire outputs are turned off before the ignition-command stage begins.
- In spark-test mode, the outputs stop immediately if either `Arm` or `Trigger` is released.
- Serial debug is disabled by default in `v006` so the production build does not accidentally stretch a microsecond-scale dwell window.

Important note:

- This software is not a substitute for a hardwired emergency stop.
- The emergency stop should physically remove power from the hot-wire supply and the spark system.
- The blocking dwell approach in `v006` improves timing accuracy, but it also means `Arm` is not re-polled during the very short dwell window itself.

## 11. Hardware Points to Confirm

Before using the controller on the real setup, two hardware questions should be confirmed:

1. `Relay polarity`
   Some relay modules are active `LOW` rather than active `HIGH`. If the relays energize when the controller output goes low, the output logic in the code must be inverted.
2. `Input wiring`
   The `Arm`, `Trigger`, and `Mode` inputs must be electrically well-defined. If the wiring allows the input to float, the controller can behave unpredictably.

## 12. Practical Test Strategy

Recommended step-by-step validation:

1. Power the M-Duino correctly from its intended external supply.
2. Connect the Mac by USB only for upload and serial monitoring.
3. Test the logic first with the hazardous power stages disconnected.
4. Use the serial monitor to check `Mode`, `Arm`, `Trigger`, and the current state name.
5. Verify relay polarity on each hot-wire channel before connecting the real hot-wire power circuit.
6. Introduce the real hot-wire and spark hardware only after the low-risk logic checks pass.

## 13. Short Summary

This reviewed version keeps the same overall purpose as the original sketch, but it is easier to understand, easier to explain, and easier to review with colleagues. The main improvements are:

- clearer naming
- explicit timing units
- a proper state machine
- deliberate safety and lockout behavior
- a clearer explanation of how hot wires, coil dwell, ignition release, and DAQ interact
- better timing-variable naming and unit visibility than the original sketch
