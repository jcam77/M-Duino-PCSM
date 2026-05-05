# Wokwi Arduino Mega Simulation For `M_Duino_v004`

This folder helps you simulate the **logic and timing flow** of
[`M_Duino_v004.ino`](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v004/M_Duino_v004.ino)
in Wokwi using an **Arduino Mega**.

`v004` differs from `v003` in one important operator behavior:

- in **spark-test mode**, `TRIGGER` is now a toggle command
- first press starts repeating spark pulses
- second press stops the repeating spark pulses
- `ARM` must still be active, and releasing `ARM` stops spark-test activity immediately

For readability, the Wokwi `v004` simulator also uses:

- `INPUT_PULLUP`
- active-low input wiring inside the simulator only

This keeps the diagram cleaner by removing extra pull-down / 5V wiring on the left side.
It does **not** change the intended operator behavior.

## Files

- [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/diagram.json)
- [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/mduino_wokwi_pins.h)
- [M_Duino_v004_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/M_Duino_v004_Wokwi.ino)
- [M_Duino_v004_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/M_Duino_v004_Wokwi_visible.ino)

## Wokwi Controls

- `ARM` slide switch:
  - left = armed
  - right = not armed
- `TRIGGER` pushbutton: momentary trigger command, key `T`
- `MODE` slide switch:
  - left = spark-test mode
  - right = hydrogen-test mode

## How To Use It In Wokwi Web

1. Create a new Arduino Mega project in Wokwi.
2. Replace the default `diagram.json` with the contents of:
   [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/diagram.json)
3. Create a second file in the Wokwi project named `mduino_wokwi_pins.h`.
4. Paste into it the contents of:
   [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/mduino_wokwi_pins.h)
5. Replace the default `sketch.ino` with the contents of:
   [M_Duino_v004_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/M_Duino_v004_Wokwi.ino)
6. Start the simulation and open the Serial Monitor.

If you want the LEDs to be clearly visible during simulation, use this file instead:

- [M_Duino_v004_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v004/M_Duino_v004_Wokwi_visible.ino)

That simulator-only variant uses:
- `hotWireBurn_us = 300 ms`
- `sparkDwell_us = 500 ms`
- `daqPulse_us = 150 ms`

## Recommended Checks In Wokwi

### Spark-test mode

1. Put `MODE` in `HIGH`.
2. Switch `ARM` on.
3. Confirm that no spark starts automatically.
4. Press `TRIGGER` once.
5. Confirm repeating spark pulses begin.
6. Press `TRIGGER` again.
7. Confirm the repeating spark pulses stop.
8. Release `ARM`.
9. Confirm all spark-test activity stops immediately.

### Hydrogen-test mode

1. Put `MODE` in `LOW`.
2. Switch `ARM` on.
3. Press `TRIGGER`.
4. Confirm this sequence:
   - `Arm Light` turns on
   - `Hot Wire 1-3` turn on for the configured burn time
   - hot-wire LEDs turn off
   - `SparkOut` turns on for the dwell interval
   - `DAQTrig` turns on near the end of the dwell interval
   - both outputs turn off
   - the controller stays locked out until `ARM` and `TRIGGER` are released

### Real hardware note about the trigger control

In the real trigger box, the `Trigger` control may be a maintained switch rather than a momentary pushbutton.

That means:

- leaving `Trigger` active is not a clean reset condition
- after a completed or failed hydrogen-test cycle, both `ARM` and `TRIGGER` should be returned to the inactive position before the next re-arm
- if `Trigger` remains active, the ready/armed indication should not be interpreted as a valid clean re-arm state

This note applies to the hydrogen-test reset behavior. In spark-test mode, the armed indication follows `ARM` more directly and does not use the same strict trigger-reset rule.
