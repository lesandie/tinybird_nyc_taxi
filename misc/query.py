import requests
import pandas as pd

# Token anonymized
params = {
    'token': '.eyJ1IjogImYxNDQzM2QxLWJhZWEtNGM5MC04ZDc1LWIxNmJiZDBkM2NjZSIsICJpZCI6ICI2NGRlZmY5Mi0xMDcyLTQ3MDYtOTQ0My02ODM1ZjE0NDE1ZGYifQ.ANDdHelFCeqlBZO9lmVxeSjrGBbW2y1ZFMVHBfEht44',
    'q':'SELECT pickup_datetime, dropoff_datetime, puzone, dozone, trip_time, passenger_count, trip_distance FROM nyc_taxi_zone_clean_pipe LIMIT 1000'
}

url = 'https://api.tinybird.co/v0/pipes/nyc_taxi_zone_clean_pipe.json'

response = requests.get(url, params=params, stream=True)
stream = response.json()
print(stream.keys())
#print(response.json()['data'])
#df = pd.DataFrame.from_dict(r, orient="index")
#df = pd.DataFrame(response.json())
#df.to_json()
#print(df.describe())