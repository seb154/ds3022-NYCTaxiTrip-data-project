import duckdb
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='load.log'
)
logger = logging.getLogger(__name__)


def load_parquet_files():

    con = None

    try:
        # Connect to local DuckDB instance
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")

        # Load vehicle emissions
        # drop table = if vehicle_emissions already exists then delete it
        # create table = create a new table called vehicle_emissions
        # select = read everything from this csv file
        con.execute("""
            DROP TABLE IF EXISTS vehicle_emissions;
            CREATE TABLE vehicle_emissions AS
            SELECT * FROM read_csv_auto(
                'data/vehicle_emissions.csv');
        """)

        n = con.execute(
            "SELECT COUNT(*) FROM vehicle_emissions"
        ).fetchone()[0]
        logger.info(f"vehicle_emissions: {n} rows loaded")

        # LOAD YELLOW TAXI CAB DATA
        # we have 12 months and need to combine all 12 into yellow_trips
        # we could have DuckDB do:
        #   CREATE TABLE yellow_trips AS
        #   SELECT * FROM read_parquet('yellow_tripdata_2024-01.parquet');
        # that would only give us January and then repeat it 11 times,
        # so it's not efficient --> FOR LOOP!

        # this is the common part of the links so we store it
        yellow_base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-"

        # Delete the old table before starting a fresh load
        con.execute("""
            DROP TABLE IF EXISTS yellow_trips;
        """)

        # RANGE: 1-12 for months SO (1, 13) so it accesses all 12
        for month in range(1, 13):
            month_string = f"{month:02d}"  # Format month as two digits
            url = f"{yellow_base_url}{month_string}.parquet"  # full link for each month

            if month == 1:
                # For the first month, create the table.
                # We select specific columns and rename them to match what we want,
                # which also keeps DuckDB from choking on the many columns in the parquet file.
                con.execute("""
                    CREATE TABLE yellow_trips AS
                    SELECT
                        VendorID,
                        tpep_pickup_datetime AS pickup_time,
                        tpep_dropoff_datetime AS dropoff_time,
                        passenger_count,
                        trip_distance
                    FROM read_parquet(?);
                """, [url])  # ? is a placeholder so we can pass the url as a parameter

            else:
                # For subsequent months, append to the table rather than creating a new one
                con.execute("""
                    INSERT INTO yellow_trips
                    SELECT
                        VendorID,
                        tpep_pickup_datetime AS pickup_time,
                        tpep_dropoff_datetime AS dropoff_time,
                        passenger_count,
                        trip_distance
                    FROM read_parquet(?);
                """, [url])
            logger.info(f"yellow_trips: loaded month {month_string}/2024")

        # Count all Yellow taxi rows after loading
        n = con.execute(
            "SELECT COUNT(*) FROM yellow_trips"
        ).fetchone()[0]

        logger.info(f"yellow_trips: {n} rows loaded")

        # LOAD GREEN TAXI CAB DATA
        # we have 12 months and need to combine all 12 into green_trips

        # common part of the Green taxi links
        green_base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2024-"

        # Delete the old table before starting a fresh load
        con.execute("""
            DROP TABLE IF EXISTS green_trips;
        """)

        # RANGE: 1-12 for months
        for month in range(1, 13):

            # Format month as two digits
            # 1 becomes "01", 2 becomes "02", etc.
            month_string = f"{month:02d}"

            # Build the full link for each month
            url = f"{green_base_url}{month_string}.parquet"

            if month == 1:

                # For the first month, create the table.
                # We select specific columns and rename them to match what we want,
                # which also keeps DuckDB from choking on the many columns in the parquet file.
                con.execute("""
                    CREATE TABLE green_trips AS
                    SELECT
                        VendorID,
                        lpep_pickup_datetime AS pickup_time,
                        lpep_dropoff_datetime AS dropoff_time,
                        passenger_count,
                        trip_distance
                    FROM read_parquet(?);
                """, [url])

            else:

                # For subsequent months, append to the table
                con.execute("""
                    INSERT INTO green_trips
                    SELECT
                        VendorID,
                        lpep_pickup_datetime AS pickup_time,
                        lpep_dropoff_datetime AS dropoff_time,
                        passenger_count,
                        trip_distance
                    FROM read_parquet(?);
                """, [url])
            logger.info(f"green_trips: loaded month {month_string}/2024")
            
        # Count all Green taxi rows after loading
        n = con.execute(
            "SELECT COUNT(*) FROM green_trips"
        ).fetchone()[0]

        logger.info(f"green_trips: {n} rows loaded")

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    load_parquet_files()