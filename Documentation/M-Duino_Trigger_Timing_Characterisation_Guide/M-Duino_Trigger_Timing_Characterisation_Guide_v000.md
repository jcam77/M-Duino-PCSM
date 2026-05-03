# M-Duino Trigger Timing Characterisation Guide

## Purpose

This document describes how to characterise the timing performance of the M-Duino when it is used as an event sequencer for a hydrogen deflagration setup.

The goal is to measure:

- the delay between an input event and the M-Duino trigger outputs
- the shot-to-shot jitter of that delay
- the relative skew between the two DAQ trigger paths and the camera trigger path

This characterisation supports the timing budget for experiments where:

- the M-Duino coordinates event timing
- the final scientific timestamping is done by a high-speed datalogger
- the camera has its own trigger path
- two DAQ systems receive the same trigger through a BNC splitter

## Scope and Interpretation

This procedure is intended for:

- hydrogen deflagration experiments
- trigger coordination validation
- pre-test system timing checks

This procedure is **not** intended to prove detonation-grade timing performance.

The main question is not whether the M-Duino is the final scientific clock.

The main question is whether it provides:

- stable trigger timing
- acceptably low jitter
- acceptably low relative skew between the connected systems

## Trigger Architecture Assumed Here

The guide assumes the following trigger arrangement:

1. An input event arrives at the M-Duino.
2. The M-Duino generates a trigger for the DAQ chain.
3. That DAQ trigger is split with a BNC splitter.
4. The split trigger goes to:
   - DAQ 1
   - DAQ 2
5. The camera is triggered through its own separate trigger path.
6. Final high-speed time-resolved data are recorded by the datalogger.

This means the timing problem has two branches:

- `M-Duino -> DAQ trigger output -> splitter -> DAQ 1 / DAQ 2`
- `M-Duino -> camera trigger output/path -> camera`

## Safety and Good Practice

- Perform this characterisation with the real trigger electronics but without ignition or hazardous experiment execution.
- Use a safe simulated input event such as a function-generator pulse or bench pulse source.
- Keep the firmware version fixed during the test campaign.
- Record all channel names, cable lengths, edge polarity, and scope settings.
- Use the same trigger edge as the real experiment.

## Required Equipment

- M-Duino controller with the test firmware version to be used experimentally
- Oscilloscope with at least 4 channels if possible
- BNC cables
- BNC splitter for the DAQ trigger path
- Safe pulse source or function generator
- Access to:
  - M-Duino input under test
  - M-Duino DAQ trigger output
  - DAQ 1 trigger input
  - DAQ 2 trigger input
  - camera trigger signal or camera trigger input line

Optional but recommended:

- logic probe or logic analyser for quick signal sanity checks
- notebook or spreadsheet for repeated timing statistics

## Signals To Measure

### Minimum measurement set

If a 4-channel oscilloscope is available:

- `CH1`: input event into the M-Duino
- `CH2`: M-Duino DAQ trigger output before the splitter
- `CH3`: DAQ 1 trigger input
- `CH4`: camera trigger signal or camera trigger input

Then repeat with:

- `CH1`: input event into the M-Duino
- `CH2`: M-Duino DAQ trigger output before the splitter
- `CH3`: DAQ 2 trigger input
- `CH4`: camera trigger signal or camera trigger input

### Preferred full characterisation

If the oscilloscope or acquisition method allows it, characterise all of these:

- input event into the M-Duino
- M-Duino DAQ trigger output before splitter
- DAQ 1 trigger input
- DAQ 2 trigger input
- camera trigger signal

## Key Timing Quantities

The following quantities should be measured.

### M-Duino internal trigger path

- `t_input_to_daq = t(M-Duino DAQ output) - t(M-Duino input)`
- `t_input_to_camera = t(camera trigger output/path) - t(M-Duino input)`

These measure the controller-side delay.

### Distribution-path timing

- `t_daq1 = t(DAQ 1 trigger input) - t(M-Duino DAQ output)`
- `t_daq2 = t(DAQ 2 trigger input) - t(M-Duino DAQ output)`

These measure the splitter and cable path contribution.

### Relative synchronisation offsets

- `skew_daq = t(DAQ 1 trigger input) - t(DAQ 2 trigger input)`
- `skew_cam_daq1 = t(camera trigger path) - t(DAQ 1 trigger input)`
- `skew_cam_daq2 = t(camera trigger path) - t(DAQ 2 trigger input)`

These are often the most important quantities for multi-system synchronisation.

## Oscilloscope Configuration

Recommended starting settings:

- trigger on the rising edge of the input event, unless the real system uses the falling edge
- use identical vertical scale settings for comparable logic signals where practical
- set the time base so the full response appears with clear edge detail
- use single-shot acquisition first to confirm signal order
- then use repeated acquisition for statistics

Recommended metadata to record:

- oscilloscope model
- probe type
- sample rate
- bandwidth limit status
- trigger mode
- trigger edge
- firmware version
- experiment mode
- date and operator

## Test Procedure

### Part A. Bench sanity check

1. Confirm all channels are connected correctly.
2. Verify the pulse source is safe and repeatable.
3. Confirm the M-Duino responds exactly as expected.
4. Verify the DAQ trigger output and camera trigger path are active and visible on the oscilloscope.

### Part B. M-Duino delay measurement

1. Connect the pulse source to the M-Duino input under test.
2. Connect the oscilloscope to the M-Duino input and trigger outputs.
3. Trigger the scope on the input edge.
4. Measure:
   - input to DAQ trigger output
   - input to camera trigger output/path
5. Repeat for at least `100` events.
6. Prefer `500` to `1000` events if the scope statistics mode supports this easily.

### Part C. DAQ splitter path measurement

1. Connect one scope channel to the M-Duino DAQ trigger output before the splitter.
2. Connect additional channels to:
   - DAQ 1 trigger input
   - DAQ 2 trigger input
3. Measure the delay from the M-Duino DAQ output to each DAQ trigger input.
4. Measure the relative skew between DAQ 1 and DAQ 2.
5. Repeat for many events and record statistics.

### Part D. Camera-to-DAQ synchronisation measurement

1. Observe the camera trigger line together with:
   - the M-Duino DAQ trigger output
   - at least one DAQ trigger input
2. Measure the relative delay between the camera trigger path and the DAQ trigger path.
3. Repeat for many events and record statistics.
4. If possible, repeat with both DAQ channels in separate runs.

## Statistics To Record

For each measured quantity, record:

- mean delay
- minimum delay
- maximum delay
- standard deviation
- peak-to-peak jitter
- number of repetitions

If your oscilloscope reports only part of these, record what is available and note the limitation.

## Recommended Results Table

| Path | Mean delay | Min | Max | Std dev | Peak-to-peak jitter | Repetitions | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Input -> M-Duino DAQ output |  |  |  |  |  |  | |
| Input -> M-Duino camera trigger path |  |  |  |  |  |  | |
| M-Duino DAQ output -> DAQ 1 input |  |  |  |  |  |  | |
| M-Duino DAQ output -> DAQ 2 input |  |  |  |  |  |  | |
| DAQ 1 input -> DAQ 2 input |  |  |  |  |  |  | Relative skew |
| Camera trigger path -> DAQ 1 input |  |  |  |  |  |  | Relative skew |
| Camera trigger path -> DAQ 2 input |  |  |  |  |  |  | Relative skew |

## Timing Budget Interpretation

For this application, the M-Duino is used mainly as an event coordinator rather than the final scientific timing reference.

The timing budget should therefore focus on:

- trigger delay stability
- trigger jitter
- relative skew between systems

A practical interpretation is:

`Total synchronisation uncertainty ~= controller jitter + branch skew + device trigger-response jitter`

In many deflagration experiments, a fixed offset is less problematic than variable offset.

This means:

- a constant delay can often be corrected in analysis
- unstable shot-to-shot delay is the more serious problem

## Suggested Acceptance Logic

The system can usually be considered acceptable for deflagration synchronisation if:

- DAQ 1 and DAQ 2 receive the split trigger with negligible relative skew for the experiment needs
- the camera trigger path has a stable offset relative to the DAQ trigger path
- M-Duino shot-to-shot jitter is small compared with the timing precision required by the experiment
- the observed uncertainty is small relative to the characteristic timescales of interest

This should be judged against the actual experiment requirements, not only against generic controller data.

## Reporting Notes

When documenting the result, include:

- firmware version
- M-Duino input and output names
- trigger edge used
- cable lengths if relevant
- oscilloscope configuration
- number of repetitions
- mean and jitter statistics

## Example Report Wording

Example wording for a methods section:

> The trigger timing of the M-Duino coordination layer was characterised with an oscilloscope prior to experiments. The delay from the selected M-Duino input event to the DAQ trigger output and camera trigger path was measured over repeated trials, together with the relative skew between the two DAQ trigger inputs and the camera trigger path. Because the final scientific timestamping was performed by the high-speed datalogger, the main acceptance criterion was low and stable inter-system trigger uncertainty rather than absolute controller latency. For the present deflagration experiments, the measured trigger offsets were sufficiently stable that inter-device clock differences were considered negligible over the acquisition window.

## Test Record Template

### Test metadata

- Date:
- Operator:
- Firmware version:
- M-Duino mode:
- Input channel used:
- DAQ trigger output used:
- Camera trigger output/path:
- Oscilloscope model:
- Trigger edge:
- Sample rate:
- Repetitions:

### Observations

- Signal quality:
- Any missed triggers:
- Any inconsistent trigger edges:
- Any cable or termination notes:

### Summary judgement

- Is the DAQ splitter path sufficiently aligned?
- Is the camera path offset stable?
- Is the measured jitter acceptable for the intended deflagration work?
- Are additional tests needed before live experiments?
