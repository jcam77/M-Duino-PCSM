# M-Duino Trigger Timing Characterisation Guide

## Purpose

This guide explains, in practical terms, how to measure the timing behaviour of the M-Duino when it is used as a trigger coordinator for a hydrogen deflagration setup.

The aim is to determine:

- the delay between the event arriving at the M-Duino and the trigger outputs leaving it
- the shot-to-shot jitter of those delays
- the relative timing skew between:
  - the two DAQ trigger branches
  - the DAQ trigger path and the camera trigger path

This is useful because the M-Duino is not the final scientific timing reference in your setup. The final scientific time base is provided by the high-speed datalogger. The M-Duino is instead the device that distributes coordinated trigger events.

## What This Characterisation Is Trying To Prove

This procedure is not mainly asking:

- "Is the M-Duino a perfect clock?"

It is asking:

- "Does the M-Duino distribute the trigger events with low enough uncertainty for the experiment?"

For deflagration work, that usually means checking:

- low and stable trigger delay
- low trigger jitter
- low relative skew between systems

If those are good, then the internal clocks of the connected systems may often be treated as second-order effects, especially for short acquisition windows.

## Assumed Trigger Architecture

This guide assumes the following architecture:

1. A clean input event is applied to the M-Duino.
2. The M-Duino produces a DAQ trigger output.
3. That DAQ trigger is split with a BNC splitter.
4. The splitter sends the same trigger to:
   - DAQ 1
   - DAQ 2
5. The camera is triggered through its own separate trigger path.
6. The final scientific timestamping is performed by the high-speed datalogger.

So there are really two timing branches:

- `M-Duino -> DAQ trigger output -> BNC splitter -> DAQ 1 / DAQ 2`
- `M-Duino -> camera trigger path -> camera`

## Why Each Measurement Is Needed

Each measurement answers a different question.

### 1. Input to M-Duino DAQ trigger output

This tells you:

- how long the controller takes to react to the input event
- how much that delay varies from shot to shot

This is the basic controller delay measurement.

### 2. Input to camera trigger path

This tells you:

- how long the controller takes to produce the camera trigger
- whether the camera path behaves like the DAQ path or not

This matters because the camera is not sharing the same split BNC branch as the two DAQs.

### 3. M-Duino DAQ output to DAQ 1 and DAQ 2 trigger inputs

This tells you:

- how much delay is added by the splitter path, cables, or input stages
- whether the two DAQ systems receive the same trigger at essentially the same time

This is the main synchronisation check for the split trigger path.

### 4. Camera trigger path relative to the DAQ trigger path

This tells you:

- whether the camera is offset relative to the DAQ systems
- whether that offset is stable

A stable offset is often acceptable. A variable offset is much more problematic.

## Do You Need Special Benchmark Code?

Not necessarily for the first pass.

There are two different types of timing study:

### Real system timing study

This uses:

- your real firmware
- your real trigger outputs
- your real DAQ trigger branch
- your real camera trigger path
- the oscilloscope

This is the most important study because it answers:

- "Is my actual experimental trigger system good enough?"

### Low-level benchmark timing study

This uses:

- special test code such as the kind shown in the Industrial Shields article
- simplified timing loops
- very controlled read/write measurements

This answers:

- "What is the intrinsic M-Duino timing performance under simplified conditions?"

For your case, the recommended order is:

1. Measure the real system first.
2. Use special benchmark code only if:
   - the real results are worse than expected
   - you need to separate hardware delay from firmware logic delay
   - you want a deeper methods section or technical appendix

## Safety and Measurement Validity

- Perform the test without ignition and without hazardous experiment execution.
- Use a safe, repeatable pulse source.
- Use the same firmware version intended for the experiments.
- Use the same trigger edge that will be used experimentally.
- Keep cable routing and terminations realistic.
- Record all settings carefully.

Very important:

- Do not attach oscilloscope grounds carelessly.
- Follow the lab's oscilloscope grounding rules.
- Only probe nodes that are safe for direct oscilloscope connection.
- If there is any doubt about common ground, floating circuits, or high-side measurement, use the correct differential or isolated measurement method.

If the probing method is wrong, the characterisation is not valid and could also be unsafe.

## Equipment Needed

- M-Duino controller with the intended firmware
- oscilloscope, ideally 4 channels
- probes suitable for the signal levels being measured
- BNC cables
- BNC splitter for the DAQ branch
- clean pulse source or function generator
- access to:
  - the chosen M-Duino input
  - the M-Duino DAQ trigger output
  - DAQ 1 trigger input
  - DAQ 2 trigger input
  - camera trigger signal or camera trigger input line

Recommended:

- notebook or spreadsheet for logging repeated measurements
- known cable lengths
- labels for channels and trigger paths

## Recommended Wiring Concept

### A. Controller delay measurement

Use this when measuring the controller-side delays.

```text
Pulse source
   |
   +-----------------------> CH1 on oscilloscope
   |
   +-----------------------> M-Duino input under test

M-Duino DAQ trigger output -----> CH2 on oscilloscope

M-Duino camera trigger path ----> CH3 on oscilloscope
```

This measurement gives:

- input to DAQ trigger output delay
- input to camera trigger path delay

### B. DAQ splitter path measurement

Use this when checking whether the split DAQ trigger is truly shared with low skew.

```text
M-Duino DAQ trigger output
   |
   +-----------------------> CH1 on oscilloscope
   |
   +-------> BNC splitter -------> DAQ 1 trigger input -----> CH2 on oscilloscope
                         |
                         +-------> DAQ 2 trigger input -----> CH3 on oscilloscope
```

This measurement gives:

- delay to DAQ 1
- delay to DAQ 2
- relative skew between DAQ 1 and DAQ 2

### C. Camera versus DAQ timing measurement

Use this when checking the relative timing between the camera and the DAQ systems.

```text
M-Duino DAQ trigger output --------> CH1 on oscilloscope

DAQ 1 trigger input ---------------> CH2 on oscilloscope

Camera trigger path ---------------> CH3 on oscilloscope
```

Then repeat with DAQ 2 if needed.

This measurement gives:

- camera versus DAQ relative offset
- stability of that offset over repeated shots

## Recommended Scope Channels

If you have four channels available, a good sequence is:

### Run 1. Controller delay run

- `CH1`: input event into the M-Duino
- `CH2`: M-Duino DAQ trigger output
- `CH3`: camera trigger path
- `CH4`: optional spare or another relevant node

### Run 2. DAQ splitter run

- `CH1`: M-Duino DAQ trigger output before the splitter
- `CH2`: DAQ 1 trigger input
- `CH3`: DAQ 2 trigger input
- `CH4`: optional spare

### Run 3. Camera versus DAQ run

- `CH1`: M-Duino DAQ trigger output
- `CH2`: camera trigger path
- `CH3`: DAQ 1 trigger input
- `CH4`: DAQ 2 trigger input if possible, otherwise repeat in a second run

If you cannot measure all branches at once, keep one common reference channel across runs. The best common reference is usually:

- the M-Duino DAQ trigger output before the splitter

## Exactly What To Measure On The Oscilloscope

Measure all delays using the same edge definition.

Best practice:

- use the rising edge if that is the real trigger edge
- use the falling edge only if the real system actually triggers on the falling edge
- define timing at the `50% amplitude crossing` of the edge

Why use the 50% crossing:

- it gives a consistent timing reference
- it avoids ambiguity from slightly different edge shapes

If the oscilloscope supports automatic delay measurements, use them. If not:

- place time cursors at the 50% crossing points
- use the same method for all channels

## Key Timing Quantities

### Controller-side delays

- `t_input_to_daq = t(DAQ trigger output) - t(input event)`
- `t_input_to_camera = t(camera trigger path) - t(input event)`

These tell you how the controller responds to the input event.

### Splitter-path delays

- `t_daq1 = t(DAQ 1 trigger input) - t(M-Duino DAQ output)`
- `t_daq2 = t(DAQ 2 trigger input) - t(M-Duino DAQ output)`

These tell you what happens in the distribution branch after the M-Duino.

### Relative skew quantities

- `skew_daq = t(DAQ 1 trigger input) - t(DAQ 2 trigger input)`
- `skew_cam_daq1 = t(camera trigger path) - t(DAQ 1 trigger input)`
- `skew_cam_daq2 = t(camera trigger path) - t(DAQ 2 trigger input)`

These are often the most useful final synchronisation metrics.

## Recommended Scope Configuration

- trigger on the input event for controller-delay measurements
- trigger on the M-Duino DAQ output for splitter and branch comparison measurements
- keep the vertical scale appropriate for the logic level
- use enough time resolution to see the edge cleanly
- use repeated acquisitions or statistics mode for jitter measurements
- start with single acquisitions to confirm signal order and polarity

Record:

- oscilloscope model
- probe type
- sample rate
- bandwidth setting
- trigger source
- trigger edge
- vertical scale
- horizontal scale
- firmware version
- experiment mode
- cable lengths if important

## Step-By-Step Measurement Procedure

### Part A. Validate the bench setup

1. Confirm that the pulse source produces a clean and repeatable edge.
2. Confirm that the pulse actually reaches the intended M-Duino input.
3. Confirm that the M-Duino produces the expected trigger outputs.
4. Confirm that the camera trigger line and DAQ trigger line are both visible and correctly identified.

Do not start collecting timing data until these basics are verified.

### Part B. Measure controller delay

1. Connect the pulse source to the chosen M-Duino input.
2. Probe the input event on `CH1`.
3. Probe the M-Duino DAQ trigger output on `CH2`.
4. Probe the camera trigger path on `CH3`.
5. Trigger the scope on the input event.
6. Measure:
   - `input -> DAQ trigger output`
   - `input -> camera trigger path`
7. Repeat for at least `100` shots.
8. Prefer `500` to `1000` shots if the scope statistics mode supports it.

### Part C. Measure DAQ splitter timing

1. Move `CH1` to the M-Duino DAQ trigger output before the splitter.
2. Probe DAQ 1 trigger input on `CH2`.
3. Probe DAQ 2 trigger input on `CH3`.
4. Trigger the scope on the M-Duino DAQ output.
5. Measure:
   - `DAQ output -> DAQ 1 input`
   - `DAQ output -> DAQ 2 input`
   - `DAQ 1 input -> DAQ 2 input`
6. Repeat for many shots and record statistics.

### Part D. Measure camera versus DAQ timing

1. Keep the M-Duino DAQ trigger output as the common reference.
2. Probe the camera trigger path.
3. Probe at least one DAQ trigger input.
4. Measure the relative delay between camera and DAQ paths.
5. Repeat for many shots.
6. If needed, repeat with the other DAQ input.

## How To Decide If The Measurement Is Valid

The measurement is more likely to be valid if:

- the signals are clean and repeatable
- the same edge definition is used everywhere
- the reference channel is kept consistent across repeated runs
- the same firmware and mode are used throughout the test
- the measured values do not jump around because of probing mistakes

The measurement is suspect if:

- the observed edges are noisy or rounded beyond recognition
- the trigger edge used for measurement is not the one used experimentally
- the oscilloscope reference channel changes from run to run without documentation
- the probing points are not actually the same signals used during the real experiment
- cable routing or splitter configuration differs from the real setup

## Common Mistakes To Avoid

- measuring the wrong trigger edge
- measuring before the actual output stage instead of at the real output node
- measuring only one DAQ branch and assuming the second branch is identical
- forgetting that the camera is on a different trigger path
- changing firmware or configuration during the test campaign
- using a time cursor at an arbitrary point instead of a consistent edge crossing
- failing to record which physical node was probed

## Statistics To Record

For each measured quantity, record:

- mean delay
- minimum delay
- maximum delay
- standard deviation
- peak-to-peak jitter
- number of repetitions

If the oscilloscope cannot provide all of them automatically, record what it can provide and note the limitation.

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

For your application, the M-Duino is a coordination layer, not the final scientific time base.

So the timing budget should mainly focus on:

- delay stability
- jitter
- relative branch skew

A practical approximation is:

`Total synchronisation uncertainty ~= controller jitter + branch skew + device trigger-response jitter`

For deflagration work, a stable fixed offset is often much less problematic than variable shot-to-shot offset.

That means:

- a fixed offset may often be corrected in analysis
- unstable offset is usually the more serious issue

## Suggested Acceptance Logic

The system can usually be considered acceptable for deflagration synchronisation if:

- DAQ 1 and DAQ 2 receive the split trigger with negligible relative skew for the intended experiment
- the camera path has a stable offset relative to the DAQ path
- M-Duino-trigger jitter is small compared with the timing precision required by the experiment
- the total uncertainty is small relative to the characteristic deflagration timescales of interest

## Example Report Wording

> The trigger timing of the M-Duino coordination layer was characterised with an oscilloscope prior to experiments. The delay from the selected M-Duino input event to the DAQ trigger output and to the camera trigger path was measured over repeated trials, together with the relative skew between the two DAQ trigger inputs and the camera trigger path. Because the final scientific timestamping was performed by the high-speed datalogger, the primary acceptance criterion was low and stable inter-system trigger uncertainty rather than absolute controller latency. For the present deflagration experiments, the measured trigger offsets were sufficiently stable that inter-device clock differences were considered negligible over the acquisition window.

## Test Record Template

### Test metadata

- Date:
- Operator:
- Firmware version:
- M-Duino mode:
- Input channel used:
- DAQ trigger output used:
- Camera trigger path:
- Oscilloscope model:
- Probe type:
- Trigger edge:
- Sample rate:
- Repetitions:

### Observations

- Signal quality:
- Missed triggers:
- Inconsistent edges:
- Cable and termination notes:
- Any difference from the real experiment wiring:

### Summary judgement

- Is the DAQ splitter path sufficiently aligned?
- Is the camera path offset stable?
- Is the measured jitter acceptable for the intended deflagration work?
- Is special benchmark firmware needed, or is the real-system measurement already sufficient?
