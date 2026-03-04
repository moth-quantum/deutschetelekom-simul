"""
Device Controller
Receives 3 paddle angles from TouchDesigner, controls polarization hardware or
runs simulation, returns 4 coincidence peak values.
"""

import json
import sys
import time
import os
import random
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('device_controller')

# Deployment-specific config (from .env)
DEVICE_ID = os.environ.get('DEVICE_ID', '38469684')
KINESIS_PATH = os.environ.get('KINESIS_PATH', r'C:\Program Files\Thorlabs\Kinesis')

# Hardware constants
DEFAULT_TIMEOUT_MS = 2000
VELOCITY_PERCENT = 90
CHANNEL_PAIRS = [(5, 6), (8, 7), (5, 7), (8, 6)]
COINCIDENCE_RUNTIME_S = 2
TRIGGER_LEVEL = 0.5
BINWIDTH_PS = 10
N_BINS = 10000
NUM_PADDLES = 3
MAX_ANGLE = 170
ZERO_PEAKS = [0, 0, 0, 0]

# Simulation constants
TARGET_ANGLES = [61, 80, 101]


def read_mode_from_env():
    use_hardware = os.environ.get('USE_REAL_HARDWARE', 'false').lower() == 'true'
    mode_name = 'HARDWARE' if use_hardware else 'SIMULATION'
    logger.info("Mode: %s", mode_name)
    return use_hardware


USE_REAL_HARDWARE = read_mode_from_env()

if USE_REAL_HARDWARE:
    import clr
    from System import Decimal
    import numpy as np

    clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
    clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.GenericMotorCLI.dll"))
    clr.AddReference(os.path.join(KINESIS_PATH, "ThorLabs.MotionControl.PolarizerCLI.dll"))

    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
    from Thorlabs.MotionControl.PolarizerCLI import Polarizer, PolarizerPaddles

    import TimeTagger

    logger.info("Hardware mode: CONNECTED")
else:
    logger.info("Simulation mode")


def control_real_hardware(input_values):
    """
    Controls ThorLabs polarizers and reads TimeTagger coincidence counts.

    Input: 3 paddle angles from TouchDesigner (0-170 degrees)
    Output: 4 coincidence peak values for channel pairs (5,6), (8,7), (5,7), (8,6)
    # c.f. Coincidence counts: 120, 350, 30, 1.6?k
    """
    try:
        DeviceManagerCLI.BuildDeviceList()
        device = Polarizer.CreatePolarizer(DEVICE_ID)
        device.Connect(DEVICE_ID)
        device.WaitForSettingsInitialized(DEFAULT_TIMEOUT_MS)
        device.StartPolling(DEFAULT_TIMEOUT_MS)
        time.sleep(0.5)

        vel_params = device.GetPolParams()
        vel_params.Velocity = VELOCITY_PERCENT
        device.SetPolParams(vel_params)

        # Angles arrive as 0-160 degrees, mapped from MIDI values (0-127) by TouchDesigner
        angle1, angle2, angle3 = input_values[:3]
        paddles = [PolarizerPaddles.Paddle1, PolarizerPaddles.Paddle2, PolarizerPaddles.Paddle3]
        positions = [Decimal(angle1), Decimal(angle2), Decimal(angle3)]

        for i in range(NUM_PADDLES):
            device.MoveTo(positions[i], paddles[i], DEFAULT_TIMEOUT_MS)

        logger.info("Moved paddles to: [%s, %s, %s]", angle1, angle2, angle3)

        try:
            results = get_coincidences(CHANNEL_PAIRS, runtime=COINCIDENCE_RUNTIME_S)
            peaks = [results[pair] for pair in CHANNEL_PAIRS]
            logger.info("Coincidence counts: %s", peaks)
        except Exception as e:
            logger.error("Coincidence counting error: %s", e)
            peaks = list(ZERO_PEAKS)

        for i in range(NUM_PADDLES):
            device.MoveTo(Decimal(0), paddles[i], DEFAULT_TIMEOUT_MS)

        device.StopPolling()
        device.Disconnect()

        peaks = [int(p) for p in peaks]
        return peaks

    except Exception:
        logger.exception("Hardware error")
        return list(ZERO_PEAKS)


def get_coincidences(channel_pairs, runtime=2, binwidth_ps=BINWIDTH_PS):
    """
    Measure all coincidences in parallel using a single TimeTagger instance.

    Args:
        channel_pairs: List of (ch1, ch2) tuples for coincidence counting
        runtime: Measurement time in seconds
        binwidth_ps: Width of time bins in picoseconds

    Returns:
        dict mapping (ch1, ch2) to max coincidence counts
    """
    measurement_time_ps = int(runtime * 1e12)
    results = {}
    tagger = None
    correlations = []

    try:
        tagger = TimeTagger.createTimeTagger()

        all_channels = set()
        for ch1, ch2 in channel_pairs:
            all_channels.update([ch1, ch2])

        for ch in all_channels:
            tagger.setTriggerLevel(ch, TRIGGER_LEVEL)

        for ch1, ch2 in channel_pairs:
            corr = TimeTagger.Correlation(tagger, ch1, ch2, binwidth_ps, n_bins=N_BINS)
            correlations.append((ch1, ch2, corr))

        for ch1, ch2, corr in correlations:
            corr.startFor(measurement_time_ps, clear=True)

        logger.info("Started parallel measurements for %d pairs (runtime=%ds)", len(channel_pairs), runtime)

        for ch1, ch2, corr in correlations:
            corr.waitUntilFinished()

        for ch1, ch2, corr in correlations:
            hist = corr.getData()
            max_counts = np.max(hist)
            results[(ch1, ch2)] = max_counts
            logger.debug("%d-%d: %s", ch1, ch2, max_counts)
            del corr

    except Exception:
        logger.exception("Parallel coincidence measurement error")
        for ch1, ch2 in channel_pairs:
            results[(ch1, ch2)] = 0

    finally:
        if tagger is not None:
            try:
                TimeTagger.freeTimeTagger(tagger)
            except Exception as e:
                logger.error("Failed to free TimeTagger: %s", e)

    return results


def simulate_device_interaction(input_values):
    """
    Generate simulated coincidence peaks.

    Input: 3 paddle angles from TouchDesigner (0-170 degrees)
    Output: 4 coincidence peak counts for channel pairs (5,6), (8,7), (5,7), (8,6)
    """
    angle1, angle2, angle3 = input_values[:3]

    # On the TouchDesigner side, the MIDI knob controller shows 48, 63, 80.
    if [int(angle1), int(angle2), int(angle3)] == TARGET_ANGLES:
        if random.choice([True, False]):
            peak_56, peak_87, peak_57, peak_86 = 788, 700, 35, 20
        else:
            peak_56, peak_87, peak_57, peak_86 = 35, 20, 788, 700
    else:
        peak_56 = random.randint(0, 100000)
        peak_87 = random.randint(0, 100000)
        peak_57 = random.randint(0, 100000)
        peak_86 = random.randint(0, 100000)

    return [peak_56, peak_87, peak_57, peak_86]


def process_input(input_values):
    """Route input to hardware or simulation based on current mode."""
    if len(input_values) < 3:
        raise ValueError(f"Expected 3 input values, got {len(input_values)}")

    angles = input_values[:3]
    if not all(0 <= v <= MAX_ANGLE for v in angles):
        raise ValueError(f"Angles out of safe range [0, {MAX_ANGLE}]: {angles}")

    if USE_REAL_HARDWARE:
        logger.info("HARDWARE mode: processing %s", angles)
        return control_real_hardware(angles)
    else:
        logger.info("SIMULATION mode: processing %s", angles)
        return simulate_device_interaction(angles)


if __name__ == "__main__":
    if sys.stdin.isatty():
        test_input = [45, 90, 135]
        result = process_input(test_input)
        print(json.dumps({"entanglement": result}), flush=True)
    else:
        # Long-running subprocess: read JSON lines from main.js via stdin
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                input_values = data.get('knob_values', [0, 0, 0])
                if len(input_values) >= 3:
                    output_values = process_input(input_values[:3])
                    print(json.dumps({"entanglement": output_values}), flush=True)
                else:
                    logger.warning("Expected 3 input values, got %d", len(input_values))
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON from stdin: %s", e)
            except ValueError as e:
                logger.warning("Validation error: %s", e)
            except Exception as e:
                logger.error("Error processing input: %s", e)
