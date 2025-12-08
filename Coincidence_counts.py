import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import requests
import TimeTagger
import time
import csv
import random
import os
from typing import Tuple, List
import numpy as np
import threading
#import qubell_rotators as rot
#from qubell_rotators import RotatorController
#import buttons 
import clr
from System import Decimal, Convert 

tagger = TimeTagger.createTimeTaggerVirtual()

def get_max_coincidences(channel_1, channel_2, binwidth_ps=10, measurement_time_ps=int(1e12)):
    """
    Returns the maximum number of coincidences between two channels.

    Args:
        channel_1 (int): First channel number (e.g., 1).
        channel_2 (int): Second channel number (e.g., 2).
        binwidth_ps (int): Width of each histogram bin in picoseconds.
        measurement_time_ps (int): Total measurement time in picoseconds.

    Returns:
        int: Maximum number of coincidences in any bin.
    """
    tagger = TimeTagger.createTimeTagger()
    tagger.setTriggerLevel(channel_1, 0.5)
    tagger.setTriggerLevel(channel_2, 0.5)

    corr = TimeTagger.Correlation(tagger, channel_1, channel_2, binwidth_ps, n_bins=10000)
    corr.startFor(measurement_time_ps,clear=True)
    corr.waitUntilFinished()
    time.sleep(0.5)

    hist = corr.getData()  # This is a NumPy array
    max_counts = np.max(hist)

    del corr
    del tagger

    return max_counts

print("First pair")
print("5-6=",get_max_coincidences(5, 6))
print("8-7=",get_max_coincidences(8, 7))
print("Second pair")
print("5-7=",get_max_coincidences(5, 7))
print("8-6=",get_max_coincidences(8, 6))