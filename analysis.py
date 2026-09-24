import duckdb
import logging
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="analysis.log"
)

logger = logging.getLogger(__name__)

DB_PATH = "emissions.duckdb"

TABLES = {
    "YELLOW": "yellow_trips",
    "GREEN": "green_trips"
}

DAY_NAMES = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]


#Helper function to print each result to the terminal and into the log
def report(message):
    print(message)
    logger.info(message)


#Find the single largest carbon producing trip (highest CO2 emissions)
def largest_trip(con, label, table):

    row = con.execute(f"""
        SELECT trip_co2_kgs, trip_distance, pickup_time
        FROM {table}
        ORDER BY trip_co2_kgs DESC    
        LIMIT 1         
    """).fetchone()

    report(
        f"[{label}] Largest single-trip CO2 of 2024: "
        f"{row[0]:.2f} kg "
        f"({row[1]:.2f} mi, picked up {row[2]})"
    )


#Find the most and least carbon heavy value 
def heaviest_lightest(
    con,
    label,
    table,
    column,
    description,
    names=None
):

    #allows us to find the average highest and lowest CO2 values for each "column" in one reusable function
    rows = con.execute(f"""
        SELECT
            {column},
            AVG(trip_co2_kgs) AS avg_co2
        FROM {table}
        GROUP BY {column}         
        ORDER BY avg_co2 DESC
    """).fetchall()

    pretty = lambda v: names[int(v)] if names else v #allows us to convert number to names, like 0 to Sunday

    high = rows[0]
    low = rows[-1]

    report(
        f"[{label}] Most carbon-heavy {description}: "
        f"{pretty(high[0])} "
        f"({high[1]:.3f} kg avg/trip)"
    )

    report(
        f"[{label}] Most carbon-light {description}: "
        f"{pretty(low[0])} "
        f"({low[1]:.3f} kg avg/trip)"
    )


#Create monthly CO2 totals plot for Yellow and Green taxis
def monthly_plot(con, filename="co2_by_month.png"):
    """Create a plot of monthly CO2 totals for Yellow and Green taxis."""

    #get monthly CO2 totals (sum)
    yellow_rows = con.execute("""
        SELECT month_of_year, SUM(trip_co2_kgs) AS total_co2
        FROM yellow_trips
        GROUP BY month_of_year
        ORDER BY month_of_year
    """).fetchall()

    green_rows = con.execute("""
        SELECT month_of_year, SUM(trip_co2_kgs) AS total_co2
        FROM green_trips
        GROUP BY month_of_year
        ORDER BY month_of_year
    """).fetchall()

    month_names = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]

    #change kilograms to tonnes
    yellow_totals = [row[1] / 1000.0 for row in yellow_rows]
    green_totals = [row[1] / 1000.0 for row in green_rows]

    # Create first y-axis
    fig, ax1 = plt.subplots(figsize=(10, 6))

    yellow_line, = ax1.plot(
        month_names,
        yellow_totals,
        marker="o",
        color="gold",
        label="Yellow Taxi"
    )

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Yellow Taxi CO2 (tonnes)")

    #reate second y-axis sharing the same x-axis
    ax2 = ax1.twinx()

    green_line, = ax2.plot(
        month_names,
        green_totals,
        marker="o",
        color="green",
        label="Green Taxi"
    )

    ax2.set_ylabel("Green Taxi CO2 (tonnes)")

    # Title and labels
    ax1.set_title("Total CO2 Output by Month")
    ax1.tick_params(axis="x", rotation=45)

    # Combined legend
    ax1.legend(
        [yellow_line, green_line],
        ["Yellow Taxi", "Green Taxi"],
        loc="upper left"
    )

    #save and close the plot
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)

    report(f"Plot written to {filename}")

#Run all analyses for both taxi types
def analysis():

    con = duckdb.connect(
        DB_PATH,
        read_only=True     #only doing analysis, not modifying the tables
    )

    #allows us to loop 2x as "TABLES" contains each taxi type (so 4x total)
    for label, table in TABLES.items():

        largest_trip(
            con,
            label,
            table
        )

        #the only things changing are the time categories (hour, day, week, and month)
        heaviest_lightest(
            con,
            label,
            table,
            "hour_of_day",    
            "hour of day"
        )

        heaviest_lightest(
            con,
            label,
            table,
            "day_of_week",
            "day of week",
            DAY_NAMES         #changes number to acutal day names
        )

        heaviest_lightest(
            con,
            label,
            table,
            "week_of_year",
            "week of year"
        )

        heaviest_lightest(
            con,
            label,
            table,
            "month_of_year",
            "month of year",
            MONTH_NAMES         #changes number to acutal month names
        )

    monthly_plot(con)          #creats plot for question 6

    con.close()           #closes DuckDB connection


if __name__ == "__main__":
    analysis()
