## This script is used to query the database
import psycopg2

from recommender.utils import connection_string

CONNECTION = connection_string()

Q1_QUERY = """
select p.title, s.id, s.content, s.start_time, s.end_time,
  s.embedding <-> q.embedding as distance
  from segment s
  join podcast p on s.podcast_id = p.id
  join segment q on q.id = '267:476'
  where s.id <> q.id
  order by distance
  limit 5;
"""

Q2_QUERY = """
select p.title, s.id, s.content, s.start_time, s.end_time,
  s.embedding <-> q.embedding as distance
  from segment s
  join podcast p on s.podcast_id = p.id
  join segment q on q.id = '267:476'
  where s.id <> q.id
  order by distance desc
  limit 5;
"""

Q3_QUERY = """
select p.title, s.id, s.content, s.start_time, s.end_time,
  s.embedding <-> q.embedding as distance
  from segment s
  join podcast p on s.podcast_id = p.id
  join segment q on q.id = '48:511'
  where s.id <> q.id
  order by distance
  limit 5;
"""

Q4_QUERY = """
select p.title, s.id, s.content, s.start_time, s.end_time,
  s.embedding <-> q.embedding as distance
  from segment s
  join podcast p on s.podcast_id = p.id
  join segment q on q.id = '51:56'
  where s.id <> q.id
  order by distance
  limit 5;
"""

# Q5: compare the segment against each episode's average embedding (its "centroid"),
# leaving out the episode the segment itself comes from
Q5_QUERY = """
with episode as (
  select podcast_id, avg(embedding) as embedding
    from segment
    group by podcast_id
)
select p.title, e.embedding <-> q.embedding as distance
  from episode e
  join podcast p on e.podcast_id = p.id
  join segment q on q.id = '{segment_id}'
  where e.podcast_id <> q.podcast_id
  order by distance
  limit 5;
"""

# Q6: compare the episode's centroid against every other episode's centroid
Q6_QUERY = """
with episode as (
  select podcast_id, avg(embedding) as embedding
    from segment
    group by podcast_id
)
select p.title, e.embedding <-> q.embedding as distance
  from episode e
  join podcast p on e.podcast_id = p.id
  join episode q on q.podcast_id = 'VeH7qKZr0WI'
  where e.podcast_id <> q.podcast_id
  order by distance
  limit 5;
"""

QUESTIONS = [
    ("Q1) What are the five most similar segments to segment '267:476'?", Q1_QUERY),
    ("Q2) What are the five most dissimilar segments to segment '267:476'?", Q2_QUERY),
    ("Q3) What are the five most similar segments to segment '48:511'?", Q3_QUERY),
    ("Q4) What are the five most similar segments to segment '51:56'?", Q4_QUERY),
    ("Q5a) What are the five most similar podcast episodes to segment '267:476'?",
     Q5_QUERY.format(segment_id="267:476")),
    ("Q5b) What are the five most similar podcast episodes to segment '48:511'?",
     Q5_QUERY.format(segment_id="48:511")),
    ("Q5c) What are the five most similar podcast episodes to segment '51:56'?",
     Q5_QUERY.format(segment_id="51:56")),
    ("Q6) What are the five most similar podcast episodes to episode 'VeH7qKZr0WI'?", Q6_QUERY),
]


def print_rows(cursor):
    """Print each result row as a block of 'column: value' lines, like psql's \\x mode."""
    columns = [d.name for d in cursor.description]
    width = max(len(c) for c in columns)
    for i, row in enumerate(cursor.fetchall(), start=1):
        print(f"-- result {i} --")
        for column, value in zip(columns, row):
            if isinstance(value, float):
                value = f"{value:.4f}"
            print(f"{column.rjust(width)}: {value}")


def main():
    conn = psycopg2.connect(CONNECTION)
    with conn.cursor() as cursor:
        for question, query in QUESTIONS:
            print("=" * 80)
            print(question)
            print(f"\nQuery:{query}")
            cursor.execute(query)
            print_rows(cursor)
            print()
    conn.close()


if __name__ == "__main__":
    main()
