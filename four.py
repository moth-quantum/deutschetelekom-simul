from ast import arg
import time
import numpy
import argparse

parser = argparse.ArgumentParser(description='test')
parser.add_argument('--hello')
args = parser.parse_args()

print(args.hello, flush=True)
time.sleep(1) # To ensure that the output isn't buffered.
print('I am talking from Python', flush=True)
time.sleep(1)
print('I really like Quantum Computing', flush=True)
time.sleep(1)
print('Integrating tech stack I know with Quantum Computing is more fun', flush=True)

