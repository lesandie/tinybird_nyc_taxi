queries
SELECT
        ytp.tpep_pickup_datetime AS pickup_datetime,
        ytp.tpep_dropoff_datetime AS dropoff_datetime,
        ytp.pulocationid,
        ytp.dolocationid,
        tzl.zone AS puzone,
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
    FROM yellow_tripdata_2019_q1 ytp
    JOIN taxi_zone_lookup tzl
    ON pulocationid = locationid
    