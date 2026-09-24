import duckdb
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='transform.log')
logger = logging.getLogger(__name__)

def transform_data():
    """Add CO2, average speed, and multiple extraction (from pickup_time) columns"""

    con = None

    try:
        # Connect to local DuckDB instance
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")

        # --------------------------------------------------
        # YELLOW TAXI TRANSFORMATIONS
        # --------------------------------------------------

        print("Transforming yellow_trips")
        logger.info("Transforming yellow_trips")

        #Add the 6 new columns
        con.execute("""
            ALTER TABLE yellow_trips
            ADD COLUMN trip_co2_kgs DOUBLE;

            ALTER TABLE yellow_trips
            ADD COLUMN avg_mph DOUBLE;

            ALTER TABLE yellow_trips
            ADD COLUMN hour_of_day INTEGER;

            ALTER TABLE yellow_trips
            ADD COLUMN day_of_week INTEGER;

            ALTER TABLE yellow_trips
            ADD COLUMN week_of_year INTEGER;

            ALTER TABLE yellow_trips
            ADD COLUMN month_of_year INTEGER;
        """)

        #Caclutae CO2
        con.execute("""
            UPDATE yellow_trips
            SET trip_co2_kgs = (
                trip_distance *
                (
                    SELECT co2_grams_per_mile
                    FROM vehicle_emissions
                    WHERE vehicle_type = 'yellow_taxi'
                )
            ) / 1000;
        """)

        #Calculate average mph
        con.execute("""
            UPDATE yellow_trips
            SET avg_mph =
                trip_distance /
                (
                    date_diff(
                        'second',
                        pickup_time,
                        dropoff_time
                    ) / 3600.0
                );
        """)

        #Extract hour of day, day of week, wekk of year, and month of year from pickup_time
        con.execute("""
            UPDATE yellow_trips
            SET
                hour_of_day = date_part('hour', pickup_time),
                day_of_week = date_part('dow', pickup_time),
                week_of_year = date_part('week', pickup_time),
                month_of_year = date_part('month', pickup_time);
        """)

        # --------------------------------------------------
        # GREEN TAXI TRANSFORMATIONS
        # --------------------------------------------------

        print("Transforming green_trips")
        logger.info("Transforming green_trips")

        #Add the 6 new columns
        con.execute("""
            ALTER TABLE green_trips
            ADD COLUMN trip_co2_kgs DOUBLE;

            ALTER TABLE green_trips
            ADD COLUMN avg_mph DOUBLE;

            ALTER TABLE green_trips
            ADD COLUMN hour_of_day INTEGER;

            ALTER TABLE green_trips
            ADD COLUMN day_of_week INTEGER;

            ALTER TABLE green_trips
            ADD COLUMN week_of_year INTEGER;

            ALTER TABLE green_trips
            ADD COLUMN month_of_year INTEGER;
        """)

        #Caclutae CO2
        con.execute("""
            UPDATE green_trips
            SET trip_co2_kgs = (
                trip_distance *
                (
                    SELECT co2_grams_per_mile
                    FROM vehicle_emissions
                    WHERE vehicle_type = 'green_taxi'
                )
            ) / 1000;
        """)

        #Calculate average mph
        con.execute("""
            UPDATE green_trips
            SET avg_mph =
                trip_distance /
                (
                    date_diff(
                        'second',
                        pickup_time,
                        dropoff_time
                    ) / 3600.0
                );
        """)

        #Extract hour of day, day of week, wekk of year, and month of year from pickup_time
        con.execute("""
            UPDATE green_trips
            SET
                hour_of_day = date_part('hour', pickup_time),
                day_of_week = date_part('dow', pickup_time),
                week_of_year = date_part('week', pickup_time),
                month_of_year = date_part('month', pickup_time);
        """)

    except Exception as e:
        print(f"An error occured: {e}")
        logger.error(f"An error occured: {e}")

if __name__ == "__main__":
    transform_data()