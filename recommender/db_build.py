## This script is used to create the tables in the database

import os
from dotenv import load_dotenv
import psycopg2

from recommender.utils import connection_string

load_dotenv()

CONNECTION = connection_string()

# need to run this to enable vector data type
CREATE_EXTENSION = "CREATE EXTENSION if not exists vector"

CREATE_PODCAST_TABLE = """
create table podcast (
  id varchar(11) primary key,
  title text not null
);
"""

CREATE_SEGMENT_TABLE = """
create table segment (
  id varchar(8) primary key,
  start_time float not null,
  end_time float not null,
  content text not null,
  embedding vector(128) not null,
  podcast_id varchar(11) not null,
  foreign key (podcast_id) references podcast(id)
);
"""

CREATE_SEGMENT_INDEX = """
create index on segment (podcast_id);
"""

conn = psycopg2.connect(CONNECTION)

cursor = conn.cursor()
cursor.execute(CREATE_EXTENSION)
cursor.execute(CREATE_PODCAST_TABLE)
cursor.execute(CREATE_SEGMENT_TABLE)
cursor.execute(CREATE_SEGMENT_INDEX)
conn.commit()
cursor.close()
conn.close()

