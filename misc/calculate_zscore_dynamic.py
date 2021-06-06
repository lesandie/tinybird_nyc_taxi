import requests
import json

# Token anonymized first calculate the avg and std from the materialized view
params = {
    'token': '.eyJ1IjogImYxNDQzM2QxLWJhZWEtNGM5MC04ZDc1LWIxNmJiZDBkM2NjZSIsICJpZCI6ICI2NGRlZmY5Mi0xMDcyLTQ3MDYtOTQ0My02ODM1ZjE0NDE1ZGYifQ.ANDdHelFCeqlBZO9lmVxeSjrGBbW2y1ZFMVHBfEht44',
    'q':"SELECT avg(passenger_count) AS avg_passenger, avg(trip_distance) AS avg_distance, avg(dateDiff('minute',pickup_datetime,dropoff_datetime)) AS avg_time, stddevPop(passenger_count) AS std_passenger, stddevPop(trip_distance) AS std_distance, stddevPop(dateDiff('minute',pickup_datetime,dropoff_datetime)) AS std_time FROM nyc_taxi_zone_clean_pipe"
}

#curl -d https://api.tinybird.co/v0/pipes/tr_pipe?lim=20&token=....
# API endpoit url
url = f'https://api.tinybird.co/v0/pipes/nyc_taxi_zone_clean_pipe.json'

response = requests.get(url, params=params)
result = response.json()
# To check if the query executed correctly
#
#print(result.keys())
#print(result.values())
#result = {result['data']:item for item in data}
params = {
    'token': '.eyJ1IjogImYxNDQzM2QxLWJhZWEtNGM5MC04ZDc1LWIxNmJiZDBkM2NjZSIsICJpZCI6ICI2NGRlZmY5Mi0xMDcyLTQ3MDYtOTQ0My02ODM1ZjE0NDE1ZGYifQ.ANDdHelFCeqlBZO9lmVxeSjrGBbW2y1ZFMVHBfEht44',
    'avg_time': result['data'][0]['avg_time'],
    'std_time': result['data'][0]['std_time'],
    'avg_passenger': result['data'][0]['avg_passenger'],
    'std_passenger': result['data'][0]['std_passenger'],
    'avg_distance': result['data'][0]['avg_distance'],
    'std_distance': result['data'][0]['std_distance']
}

response = requests.get(url, params=params)
final_result = response.json()
print(final_result['data'])