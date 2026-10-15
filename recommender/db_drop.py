## This script is used to drop the tables in the database

import os
from dotenv import load_dotenv
import psycopg2

from recommender.utils import connection_string

load_dotenv()

CONNECTION = connection_string()

# segment references podcast, so it must be dropped first (or together, as here)
DROP_TABLE = "DROP TABLE IF EXISTS segment, podcast"

with psycopg2.connect(CONNECTION) as conn:
    cursor = conn.cursor()
    cursor.execute(DROP_TABLE)
conn.close()
