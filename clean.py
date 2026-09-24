import duckdb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='clean.log')
logger = logging.getLogger(__name__)

def clean_data():

    con = None


    try:
        # Connect to local DuckDB instance
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")

        #CLEAN dataset 
        for trips in ['yellow_trips','green_trips']:
            print(f"Cleaning {trips}")

            ####1:REMOVE any trips with 0 passengers, 0 miles in length, longer than 100 miles in length, and lasting more than 1 day in length (86400 s)####
            con.execute(f"""
                        DELETE FROM {trips} WHERE passenger_count = 0
                        OR trip_distance = 0
                        OR trip_distance > 100
                        OR date_diff('second', pickup_time, dropoff_time) > 86400;
                        """) 
            ####2:REMOVE any duplicate trips####
            con.execute(f"""
                CREATE TABLE {trips}_clean AS
                SELECT DISTINCT * FROM {trips};
                DROP TABLE {trips};
                ALTER TABLE {trips}_clean
                RENAME TO {trips}; """)

            ####3: VERIFY ####

            #Verify that no duplicate trips exist
            duplicates = con.execute(f"""
                SELECT COUNT(*)
                FROM (
                    SELECT *
                    FROM {trips}
                    GROUP BY ALL
                    HAVING COUNT(*) > 1);
            """).fetchone()[0]

            print(f"{trips} duplicate trips: {duplicates}")
            logger.info(f"{trips} duplicate trips: {duplicates}")


            #Verify that no trips have 0 passengers
            zero_passengers = con.execute(f"""
                SELECT COUNT(*)
                FROM {trips}
                WHERE passenger_count = 0;
            """).fetchone()[0]

            print(f"{trips} 0-passenger trips: {zero_passengers}")
            logger.info(f"{trips} 0-passenger trips: {zero_passengers}")

            #Verify that no trips have 0 miles in length 
            zero_miles = con.execute(f"""
                SELECT COUNT(*)
                FROM {trips}
                WHERE trip_distance = 0; 
            """).fetchone()[0]

            print(f"{trips} 0-mile trips: {zero_miles}")
            logger.info(f"{trips} 0-mile trips: {zero_miles}")

            #Verify that no trips have longer than 100 miles in length
            over_100_miles = con.execute(f"""
                SELECT COUNT(*)
                FROM {trips}
                WHERE trip_distance > 100;
            """).fetchone()[0]

            print(f"{trips} over-100-mile trips: {over_100_miles}")
            logger.info(f"{trips} over-100-mile trips: {over_100_miles}")

            #Verify that no trips lasting more than 1 day in length
            over_one_day = con.execute(f"""
                SELECT COUNT(*)
                FROM {trips}
                WHERE date_diff(
                    'second',
                    pickup_time,
                    dropoff_time
                ) > 86400;
            """).fetchone()[0]

            print(f"{trips} over-86400s trips: {over_one_day}")
            logger.info(f"{trips} over-86400s trips: {over_one_day}")

    except Exception as e:
        print(f"An error occured:{e}")
        logger.error(f"An error occured: {e}")

if __name__ == "__main__":
    clean_data()


