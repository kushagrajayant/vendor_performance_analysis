import duckdb
import os
import logging
import time

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)",
    filemode="a",
    force=True
)

con = duckdb.connect("inventory.duckdb")

def load_raw_data():
    start = time.time()
    
    for file in os.listdir("data"):
        if file.endswith(".csv"):
            table_name = file[:-4] 
            
            con.execute(f""" 
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('data/{file}')
            """)

    end =time.time()
    total_time = (end - start) / 60
    
    logging.info("Execution Complete")
    logging.info(f"Total Time Taken: {total_time} minutes")

load_raw_data()