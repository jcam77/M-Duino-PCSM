# M-Duino-PCSM Project Brief

## Project Name

`M-Duino-PCSM`

Subtitle:

`Parameter Control and Status Monitoring`

## Purpose

Create a desktop/web-style control interface for the M-Duino test controller that allows the operator to:

- change approved test parameters between runs
- monitor controller status
- view state transitions and event messages
- preserve the institute visual identity used in the DIME Toolbox

The app is **not** intended to replace the M-Duino sequence logic.

## Agreed System Architecture

### M-Duino responsibilities

The M-Duino firmware remains responsible for:

- arming logic
- firing sequence logic
- hot-wire timing
- spark timing
- DAQ timing
- fail / abort / fired lockout behavior
- parameter validation and safety limits

### PC app responsibilities

The Python app is only a supervisory layer for:

- parameter editing
- parameter readback
- live status display
- event / transition log display
- serial communication with the M-Duino

### Important rule

The Python app must **not** directly run the real-time firing sequence.

The M-Duino remains the real controller.

## Hardware and Firmware Baseline

### Target hardware

The app is intended to connect to:

- `Industrial Shields M-Duino 19R+`

### Current code references

- `Original reference code`
  `M-DuinoScripts/M-Duino_Original/M-Duino_Original.ino`

- `Current cleaned controller code baseline`
  `M-DuinoScripts/M_Duino_v005/M_Duino_v005.ino`

### Why the cleaned code is the current baseline

`M_Duino_v005.ino` should be treated as the firmware baseline for app integration because it already includes:

- explicit timing variable names with units
- commented sequence logic
- named controller states
- clearer separation between logic flags and output pins
- debug-oriented state transition logging
- spark-test toggle control
- a `30 s` spark-test safety timeout

### Firmware dependency

The Python app cannot work correctly against arbitrary firmware.

It requires a compatible M-Duino firmware version that exposes:

- the agreed parameter names
- the agreed status fields
- the agreed serial command interface
- the agreed validation and safety behavior

## Connection Target and Communication Assumptions

### Connection target

The app connects to the M-Duino controller itself, not directly to:

- the hot-wire power supply
- the spark hardware
- the DAQ hardware

### Connection method

Primary connection method:

- `USB serial`

### Power assumption

The M-Duino remains powered from its proper external supply.

The USB connection is used for:

- parameter exchange
- status monitoring
- event logging

### Communication role

The app is intended to:

- send approved parameter values
- request current parameter values
- request live status
- display state transitions and reasons

The app is not intended to:

- run the firing sequence timing directly
- bypass firmware safety logic
- edit parameters during an active firing sequence

## Why This Architecture Was Chosen

This architecture is preferred over LabVIEW-only sequence control because:

- the M-Duino continues running safely if the laptop freezes or disconnects
- real-time timing stays inside the controller
- the system is easier to validate
- parameter tuning between tests is still possible without reflashing firmware

## Runtime Parameter Strategy

The M-Duino firmware should be compiled once with support for runtime parameter updates over serial.

The Python app will send new values as serial commands.

This means:

- no binary patching
- no searching inside compiled code
- no reflashing just to change a test setting

## Critical Interface Requirement

The app and the M-Duino firmware will only work together if they share a stable interface definition.

That shared interface must define:

- which parameters exist
- what each parameter is called
- what unit each parameter uses
- what range each parameter allows
- when each parameter may be changed
- which status fields are available
- which error responses may be returned

Without this mapping, the app cannot safely change values or interpret controller feedback.

## Firmware Variable / Protocol / UI Mapping Principle

The app does not edit compiled binary values directly.

Instead, the firmware must expose an external command vocabulary that maps to internal variables.

### Example concept

- `Firmware variable`
  `hotWireBurn_us`

- `Protocol name`
  `HOTWIRE_US`

- `UI label`
  `Hot-wire burn time`

All editable values should follow this three-layer mapping.

## Candidate Editable Parameters

The first version should allow editing of:

- `hotWireBurn_us`
- `sparkDwell_us`
- `daqPulse_us`
- `sparkTestInterval_us`
- `useHotWireStep`

### Suggested operator-facing units

- Hot-wire burn time: `s`
- Spark dwell: `us`
- DAQ pulse width: `us`
- Spark-test interval: `ms`
- Use hot-wire step: `true/false`

## Initial Parameter Mapping Table

| Firmware variable | Protocol name | Operator-facing label | UI unit | Notes |
|---|---|---|---|---|
| `hotWireBurn_us` | `HOTWIRE_US` | Hot-wire burn time | `s` | Main tuning parameter |
| `sparkDwell_us` | `SPARK_US` | Spark dwell | `us` | Spark pulse duration |
| `daqPulse_us` | `DAQ_US` | DAQ pulse width | `us` | Must not exceed spark dwell |
| `sparkTestInterval_us` | `SPARKTEST_US` | Spark-test interval | `ms` | Used in spark-test mode |
| `useHotWireStep` | `USE_HOTWIRE` | Use hot-wire step | `bool` | Enables or skips melting stage |

This table must remain synchronized between:

- the M-Duino firmware
- the serial protocol specification
- the Python app

If one side changes without the others, parameter control will break.

## Candidate Live Status Fields

The app should keep these values visible:

- controller state
- mode
- arm input
- trigger input
- last reason / last error
- connection status

Useful extras:

- spark active
- DAQ active
- currently loaded parameters
- timestamp of last state change

## Initial Status Contract

At minimum, the firmware should expose enough information for the app to display:

- current controller state
- current operating mode
- current Arm input state
- current Trigger input state
- last transition reason
- whether the loaded parameter set was accepted

Recommended additional status fields:

- Spark output active
- DAQ output active
- hot-wire step enabled
- startup configuration summary
- firmware version identifier

## Serial Protocol Direction

The planned communication approach is a simple text-based serial protocol.

### Example commands

```text
GET ALL
STATUS?
SET HOTWIRE_US 15000000
SET SPARK_US 5000
SET DAQ_US 600
SET SPARKTEST_US 500000
SET USE_HOTWIRE 1
```

### Example responses

```text
OK
ERROR NOT_IDLE
ERROR OUT_OF_RANGE
VALUE HOTWIRE_US 15000000
STATE IDLE
MODE HYDROGEN_TEST
ARM 0
TRIGGER 0
REASON operator reset after fired state
```

### Safety behavior

Parameter updates should only be accepted when the controller is in a safe state such as:

- `IDLE`

The M-Duino should reject invalid values and reject edits during active or locked states.

Recommended validation rules:

- reject values outside approved limits
- reject `daqPulse_us > sparkDwell_us`
- reject malformed commands
- reject edits while not in `IDLE`
- return explicit error text for operator visibility

## App Behavior Requirements

For the app to work properly as intended, it should:

- detect available serial ports
- let the operator choose the correct M-Duino port
- connect and disconnect cleanly
- request current values on connect
- show the latest controller state continuously
- show whether a parameter update was accepted or rejected
- show the returned reason or error message
- keep a readable event log
- avoid allowing unsafe parameter edits in the UI

## Firmware Behavior Requirements

For the app to work properly as intended, the firmware should:

- expose the parameter interface over serial
- expose live status over serial
- expose readable reasons for transitions or rejections
- enforce safe-state restrictions for parameter changes
- validate all incoming values
- keep the firing logic local to the M-Duino
- provide a stable naming convention for all exposed values

## Planned Python App Stack

Preferred implementation:

- `Python`
- `Panel`
- `pyserial`

This was chosen because it is open source, flexible, and well suited for a parameter-and-status dashboard.

## Visual Design Direction

The app should follow the institute style already used in the DIME Toolbox.

### Agreed naming

App title:

- `M-Duino-PCSM`

Subtitle:

- `Parameter Control and Status Monitoring`

### DIME Toolbox style cues to reuse

- Institute logo included in the header
- `Inter` as the main UI font
- `JetBrains Mono` for technical or console-style text where useful
- warm off-white page background
- warm light gray surfaces/cards
- charcoal text
- charcoal top bar
- restrained crimson accent
- minimal shadows
- crisp borders
- professional research-tool feel

### Design tokens extracted from DIME Toolbox

- Page background: `#F7F7F5`
- Surface/card: `#EEEEEA`
- Main text: `#333333`
- Muted text: `#888888`
- Top bar: `#2E2E2E`
- Secondary chrome: `#3A3A3A`
- Accent crimson: `#CC2222`
- Accent light: `#F9E5E5`
- Border tone: approximately `#D1D1CD`

## Proposed App Sections

The first version should have four main areas:

1. Connection panel
2. Editable parameter panel
3. Live status panel
4. Event / transition log

## First-Version Success Criteria

The first version of `M-Duino-PCSM` should be considered successful if it can:

1. Connect to the M-Duino over USB serial
2. Read the current parameter set
3. Display the current controller state and core input status
4. Send a new parameter value while the controller is in `IDLE`
5. Receive and display acceptance or rejection from the firmware
6. Show a readable event or transition log
7. Preserve the institute visual identity from DIME Toolbox

## Non-Goals for First Version

The first version should **not** try to do all of the following:

- run the firing sequence directly from the PC
- modify settings during an active firing cycle
- expose every low-level firmware setting
- replace hardwired safety systems

## Documentation to Preserve

The following project context already exists and should be kept with the project:

- cleaned M-Duino code documentation
- original-code review documentation
- trigger-box sequence diagrams
- original-code expected-sequence diagram
- controller code baseline references
- parameter / protocol mapping rules

## Next Recommended Steps

1. Create the GitHub repository for `M-Duino-PCSM`
2. Move or copy this brief into that repository
3. Write the formal serial interface specification
4. Update the M-Duino firmware to support safe runtime parameter updates
5. Create the first Python Panel UI scaffold
6. Add the institute logo and DIME-style theme tokens to the app

## Current Status

This brief captures the key project decisions made before starting repository implementation.
