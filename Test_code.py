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

def get_single_photons(list_channel):
    """
    Measures single photon counts for either NIR or Telecom channel using TimeTagger.
    
    Args:
        channel (str): Either 'nir' or 'tel' to select the desired photon count.
        
    Returns:
        int: Count of detected photons on the selected channel.
    """
    # Create TimeTagger instance
    tagger = TimeTagger.createTimeTagger()
    tagger.setTriggerLevel(5, 0.5)
    tagger.setTriggerLevel(8, 0.5)

    # Set measurement time in picoseconds
    measurement_time = int(1e12)  # 1 second

    # Create Counter for channels 1 (Telecom) and 2 (NIR)
    counter = TimeTagger.Counter(tagger, list_channel, measurement_time, n_values=1)

    # Wait for data to be collected
    time.sleep(1.5)

    # Get the data
    counts = counter.getData()
    #singlecount= counts[channel-1][0]
    #nir_counts = counts[1][0]

    # Clean up
    del counter
    del tagger
    return counts

list_channel=[1,2,3,4,5,6,7,8]
l=get_single_photons(list_channel)
print("1=",l[0],"2=",l[1],"3=",l[2],"4=",l[3],"5=",l[4],"6=",l[5],"7=",l[6],"8=",l[7])