# Wokwi Arduino Mega Simulation For `M_Duino_v005`

This folder helps you simulate the **logic and timing flow** of
[`M_Duino_v005.ino`](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v005/M_Duino_v005.ino)
in Wokwi using an **Arduino Mega**.

`v005` differs from `v004` in one important safety behavior:

- in **spark-test mode**, `TRIGGER` still acts as a toggle command
- first press starts repeating spark pulses
- second press stops the repeating spark pulses
- `ARM` must still be active, and releasing `ARM` stops spark-test activity immediately
- a safety timeout now also stops spark-test automatically after `30 s`

For readability, the Wokwi `v005` simulator also uses:

- `INPUT_PULLUP`
- active-low input wiring inside the simulator only

This keeps the diagram cleaner by removing extra pull-down / 5V wiring on the left side.
It does **not** change the intended operator behavior.

## Files

- [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/diagram.json)
- [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/mduino_wokwi_pins.h)
- [M_Duino_v005_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/M_Duino_v005_Wokwi.ino)
- [M_Duino_v005_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/M_Duino_v005_Wokwi_visible.ino)

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
   [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/diagram.json)
3. Create a second file in the Wokwi project named `mduino_wokwi_pins.h`.
4. Paste into it the contents of:
   [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/mduino_wokwi_pins.h)
5. Replace the default `sketch.ino` with the contents of:
   [M_Duino_v005_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/M_Duino_v005_Wokwi.ino)
6. Start the simulation and open the Serial Monitor.

If you want the LEDs to be clearly visible during simulation, use this file instead:

- [M_Duino_v005_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v005/M_Duino_v005_Wokwi_visible.ino)

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
8. Start spark-test again and let it run.
9. Confirm it stops automatically after the safety timeout.
10. Release `ARM`.
11. Confirm all spark-test activity stops immediately.

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
