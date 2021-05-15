# NYC Yellow taxi problem


## Problem Context

The data consists of a set of CSV files with yellow taxi trip records. The TLC Authority web provides a brief description of the dataset:
“Records include fields capturing pick-up and drop-off dates/times, pick-up and drop-off locations, trip distances, itemized fares, rate types, payment types, and driver-reported passenger counts. The records were collected and provided to the NYC Taxi and Limousine Commission (TLC) by technology service providers. The trip data was not created by the TLC, and TLC cannot guarantee their accuracy.“

The last part about the accuracy is very true. For the 2019’s dataset I found different dates from other years that 2019. So following some best practices we should “clean” the dataset before starting our work and thus we reduce the number of outliers cleaning beforehand.
 
So, to get a glipmse of the dataset structure we have to take a look at the data dictionary, also provided by the TCL Authority: 

https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

After that, we can see that we have to work with some Datetime types from the pickup and dropoff columns. Also other important properties for our problem are the PuLocationID and the DoLocationID. As they are ids and we need to get the zone name (text) for our study results. The zone name is not in the dataset, and we have to get it from another descriptive dataset as stated in the TLC Authority website: 

“PULocationid & DOLocationID—matching zone numbers to the map Each of the trip records contains a field corresponding to the location of the pickup or drop-off of the trip (or in FHV records before 2017, just the pickup), populated by numbers ranging from 1-263. These numbers correspond to taxi zones, which may be downloaded as a table or map/shapefile and matched to the trip records using a join. The data is currently available on the Open Data Portal at: https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc”

If we inspect the new table with the zone names we can see that the we indeed need to join both datasets to get the zone name, as stated in the description above. 

## Using the tinybird platform to get the solution
So as we are going to Tinybird as our analytics platform we need to create a couple of datasources, using the cli tool: one for the main yellow taxi trips and another for the zone name matching.

It is advisable to check the Cli tool tutorial at https://docs.tinybird.co/cli.html

First, we have to download, from the TLC website the first 3 months CSVs from 2019 year. 
Next, we are going to create a main datasource named yellow_tripdata_2019_q1 and another one for matching the zones with the name taxi_zone_lookup:

Then we need to append the next two months to the datasource with `tb datasource append` and create another datasource for the matching zones (taxi_zone_lookup).

The main problem we’re trying to solve is to obtain the outliers for the trips between two zones, but before tackling the main problem we need to clean and prepare the dataset. The main prerequisite is that the output should look something like this: 

```bash
------------------------------------------
pickup_datetime: 2019-03-29 12:36:26
dropoff_datetime: 2019-03-29 12:51:42
puzone: Yorkville West
dozone: Upper East Side North 
passenger_count: 1
trip_distance: 3.29
ratecodeid: 1
store_and_fwd_flag: N
payment_type: 1
fare_amount: 13.5
extra: 0.5
mta_tax: 0.5
tip_amount: 3.46
tolls_amount: 0
improvement_surcharge: 0.3
total_amount: 20.76
congestion_surcharge: 2.5
------------------------------------------
```
And not like this

```bash
vendorid: 2
tpep_pickup_datetime: 2019-03-29 12:36:26
tpep_dropoff_datetime: 2019-03-29 12:51:42
pulocationid: 230
dolocationid: 262
passenger_count: 1
trip_distance: 3.29
ratecodeid: 1
store_and_fwd_flag: N
payment_type: 1
fare_amount: 13.5
extra: 0.5
mta_tax: 0.5
tip_amount: 3.46
tolls_amount: 0
improvement_surcharge: 0.3
total_amount: 20.76
congestion_surcharge: 2.5
```

So we first create a new source to clean and prepare the data and this new source will have the pickup and dropoff zone names added. Tinybird can manage Materialized views, a very nice tool to ingest and transform data on the fly. Materialized views are recommended for this type of work: ingest data and add new aggregated or joined columns from another datasource (denormalize). Aggregate and Joins are expensive operations that we can do it once, during the ingesting process and leave the dataset optimized for the analytic operations.

Again we use the cli tool to create this datasource by creating a file in the datasource directory that reads like:

```sql
SCHEMA >
    `pickup_datetime` DateTime,
    `dropoff_datetime` DateTime,
    `pulocationid` Int32,
    `dolocationid` Int32,
    `puzone` String,
    `dozone` String,
    `passenger_count` Int16,
    `trip_distance` Float32,
    `ratecodeid` Int16,
    `payment_type` Int16,
    `fare_amount` Int32,
    `extra` Int32,
    `mta_tax` Int32,
    `tip_amount` Int32,
    `tolls_amount` Int32,
    `total_amount` Int32

ENGINE "MergeTree"
ENGINE_SORTING_KEY "pickup_datetime, dropoff_datetime"
```

Because we’re going to join two datasources we should be using clickhouse’s JOIN engine for our materialized view, but due to that the “dimension” taxi_zone_names table has a few rows
SELECT count(*) FROM taxi_zone_lookup (256) the performance difference would be neglegible if using the mergetree engine. On the contrary if we had a pretty bigger fact and dimension tables then it would be more performant to use the Join engine. Nevertheless I created the data source with the join engine and a pipe to test the performance. You can find it in the repo code with the names nyc_taxi_join and nyc_taxi_join_pipe.

The query with the joined data in a executes in 31.74ms processing 23M rows, in
```sql
SELECT
        ytp.tpep_pickup_datetime AS pickup_datetime,
        ytp.tpep_dropoff_datetime AS dropoff_datetime,
        ytp.pulocationid,
        ytp.dolocationid,
        tzu.zone AS puzone,
        tzo.zone AS dozone,
        ytp.passenger_count,
        ytp.trip_distance,
        ytp.ratecodeid,
        ytp.payment_type,
        ytp.fare_amount,
        ytp.extra,
        ytp.mta_tax,
        ytp.tip_amount,
        ytp.tolls_amount,
        ytp.total_amount
    FROM yellow_tripdata_2019_q1 ytp
    INNER JOIN taxi_zone_lookup tzu ON ytp.pulocationid = tzu.locationid
    INNER JOIN taxi_zone_lookup tzo ON ytp.dolocationid = tzo.locationid
```

After that we need a pipe to transform and clean the data until we get to the desired dataset state to begin with the main problem.

The pipe:

```sql
NODE select_zone_name
DESCRIPTION>
Joins the two datasources into a materialized view with two new columns with the pickup and dropoff zone names (puzone, do zone)
SQL >

    SELECT
        ytp.tpep_pickup_datetime AS pickup_datetime,
        ytp.tpep_dropoff_datetime AS dropoff_datetime,
        ytp.pulocationid AS pulocationid,
        ytp.dolocationid AS dolocationid,
        tzu.zone AS puzone,
        tzo.zone AS dozone,
        ytp.passenger_count AS passenger_count,
        ytp.trip_distance AS trip_distance,
        ytp.ratecodeid AS ratecodeid,
        ytp.payment_type AS payment_type,
        ytp.fare_amount AS fare_amount,
        ytp.extra AS extra,
        ytp.mta_tax AS mta_tax,
        ytp.tip_amount AS tip_amount,
        ytp.tolls_amount AS tolls_amount,
        ytp.total_amount AS total_amount
    FROM yellow_tripdata_2019_q1 ytp
    JOIN taxi_zone_lookup tzu ON ytp.pulocationid = tzu.locationid
    JOIN taxi_zone_lookup tzo ON ytp.dolocationid = tzo.locationid

NODE different_zones_2019
DESCRIPTION>
Gettting only the 2019 trips between different zones

SQL >
    SELECT pickup_datetime,
            dropoff_datetime,
            pulocationid,
            dolocationid,
            puzone,
            dozone,
            passenger_count,
            trip_distance,
            ratecodeid,
            payment_type,
            fare_amount,
            extra,
            mta_tax,
            tip_amount,
            tolls_amount,
            total_amount
    FROM select_zone_name 
    WHERE pulocationid != dolocationid AND 
            toYear(pickup_datetime) = 2019 AND 
            toYear(dropoff_datetime) = 2019 

TYPE materialized
DATASOURCE  nyc_taxi_zone_clean
```

## Describing and solving the main problem

Now the main problem is this: we have to get the trip outliers between any two different zones. 
For the sake of simplicity of our model i’m goint to explain what an outlier value is and how to simply detect them using simple statistical concepts like mean and standard deviation.

Outliers or anomalies are values that are out of the normal distribution of the dataset. Having a quick look at the dataset we can see that there are trips with different pickup and dropoff dates (> than 8h of trip in manhattan?) or a passenger_count of 9, when the average passenger is between 1 and 2. So we have detect these anomalies with a couple of easy statistical functions. The original dataset has many variables (columns) that can be studied like fare_amount but for the sake of the simplicity we’re going to work with the passenger_count and trip_distance. We can extrapolate this  model to work other variables like fare_amount.

A good place to start looking for a reasonable value are the mean and we can use the standard deviation to get a range of possible values. Also with these two values we can build a score to detect if a value is within an acceptable range: The z-score 

The Z-score or standar score is the number of standard deviations from the mean. In we work with the mean and standard deviation creating an upper and lower limit, our acceptable range will be one standard deviation from the mean: a z-score in the range ±1. With the z-score we can move the upper and lower bounds to get a more precise resultset of the outlier values.

The model for the passenger_count variable:

(passenger_count  - passenger_series_avg) / passenger_series_stddev AS passenger_zscore

So we can calculate the mean and standard deviation of the dataset for the passenger_count and trip_distance variables with a query to the materialized view:
```sql
SELECT avg(passenger_count) AS passenger_series_avg, stddevPop(passenger_count) as passenger_series_stddev FROM nyc_taxi_zone_clean.
```

We can query the avobe materialized view in our pipe to generate the z-scores for the passenger_count and trip_distance:

```sql
SELECT pickup_datetime, 
        dropoff_datetime, 
        passenger_count, 
        passenger_count - 1.5756512724734397 / 1.2302451685284468 as z_passenger, 
        trip_distance,
        trip_distance - 3.0367553475515594 / 3.8700316 as z_trip
FROM nyc_taxi_zone_clean
```

In order to test our model we’re going to calculate the z-score manually because we will have to adjust the acceptable range for the outliers. The above node of our pipe will be named calculate_z_scores: 

Now to start with a range of ±1 of the std:

```sql
SELECT *,
  z_passenger NOT BETWEEN -1 AND 1 AS is_outlier
FROM calculate_z_scores
```

With this range we get outliers for 3+ more passengers and less than 1, something not very accurate. If we bump the upper limit to 3 we begin to get more accurate results taking into account that supposedly the yellow cabs cannot ride with more than 4 passengers.
So finally the query that gives us us the outliers between different zones for the variable passenger_count is:
```sql
SELECT pickup_datetime, 
        dropoff_datetime, 
        puzone,
        dozone,
        passenger_count,
        z_passenger
FROM calculate_z_scores
WHERE z_passenger NOT BETWEEN -1 AND 3.5
```

We can get to the next and last variable of our problem that is the trip_distance.

As we can see the average of trip_distance is 3 miles with a deviation of 3.8 miles. That is where most of the distribution values are ranged. Again let’s start with the ±1 of the std:
```sql
SELECT pickup_datetime, 
        dropoff_datetime, 
        puzone,
        dozone,
        trip_distance,
        Z_trip NOT BETWEEN -1 AND 1 AS is_outlier
FROM calculate_z_scores
```

We get lots of outliers because the upper limit is very low. Taking into account that a trip from the upper east side to JFK or Laguardia Airport are 15+ miles, we should not discard this trips because there are meny of them. So raising the upper limit to 7 or 8 should do the trick and we can have a pretty solid outlier list with this rage:
```sql
SELECT pickup_datetime,
      dropoff_datetime,
      puzone,
      dozone,
      trip_distance,
      z_trip 
FROM calculate_z_scores
WHERE z_trip NOT BETWEEN -1 and 7
```

## Improvements

There is always room for improvements. I would like to automate the calculation of the standard deviation and average of the series for the trip_distance and passenger_count variables. For this we have to publish and endpoint for the materialized view and query the date from a python script that I would have to write.