import json

with open("data/UScitycodes.json") as f:
    data = json.load(f)
print(data)