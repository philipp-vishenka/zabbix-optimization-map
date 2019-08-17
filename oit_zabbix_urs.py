#!/usr/bin/python3

import argparse
import re
from json import dumps

parser = argparse.ArgumentParser()
parser.add_argument("settingsPath", type=str)
args = parser.parse_args()

data = []
file = open(args.settingsPath, "r")
fileRead = file.read().split("\n")
file.close()

for string in fileRead:
    if re.search("address=[0-9]+", string) != None:
        addr = int(re.search("[a-z]+=([0-9]+)", string)[1])
        data.append({"{#URSADDR}": addr})

print(dumps({"data": data}))
