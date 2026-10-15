## This script is used to insert data into the database
import json
import time
from pathlib import Path

import pandas as pd

from recommender.utils import connection_string, fast_pg_insert

CONNECTION = connection_string()

# the unzipped documents/ and embedding/ folders live outside the repo, in podcast-project/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

SEGMENT_COLUMNS = ["id", "start_time", "end_time", "content", "embedding", "podcast_id"]


def read_documents(path: Path) -> pd.DataFrame:
    """One row per segment from a batch_request_*.jsonl file (the requests sent to the OpenAI embeddings API)."""
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            meta = r["body"]["metadata"]
            rows.append((r["custom_id"], meta["start_time"], meta["stop_time"], r["body"]["input"],
                         meta["podcast_id"], meta["title"]))
    return pd.DataFrame(rows, columns=["id", "start_time", "end_time", "content", "podcast_id", "title"])


def read_embeddings(path: Path) -> pd.DataFrame:
    """One row per segment from an embedding file (the API's responses), with the vector in pgvector's text format."""
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r["error"] is not None or r["response"]["status_code"] != 200:
                raise ValueError(f"segment {r['custom_id']} has no embedding: {r['error']}")
            embedding = r["response"]["body"]["data"][0]["embedding"]
            # pgvector reads vectors written as '[0.1,0.2,...]', which is exactly what compact JSON produces
            rows.append((r["custom_id"], json.dumps(embedding, separators=(",", ":"))))
    return pd.DataFrame(rows, columns=["id", "embedding"])


start = time.time()

# Extract: the documents are small enough (~830k short rows) to hold in memory all at once
documents = pd.concat(
    [read_documents(p) for p in sorted((DATA_DIR / "documents").glob("batch_request_*.jsonl"))],
    ignore_index=True,
)
assert documents["id"].is_unique, "duplicate segment ids in the documents"
print(f"read {len(documents):,} segments ({time.time() - start:.0f}s)")

# Transform: every segment repeats its podcast's title, so collapse them to one row per podcast
podcasts = documents[["podcast_id", "title"]].drop_duplicates()
assert podcasts["podcast_id"].is_unique, "a podcast has more than one title"
podcasts["title"] = podcasts["title"].str.removeprefix("Podcast: ")

# Load podcasts first: segment.podcast_id is a foreign key to podcast.id
fast_pg_insert(podcasts, CONNECTION, "podcast", ["id", "title"])
print(f"inserted {len(podcasts)} podcasts ({time.time() - start:.0f}s)")

segments = documents.drop(columns="title")
del documents

# The embeddings are ~1.6 GB of JSON, so read, join and load them one file at a time to bound memory
inserted = 0
for path in sorted((DATA_DIR / "embedding").glob("*.jsonl")):
    embeddings = read_embeddings(path)
    # Join on custom_id, not line order; validate raises if an id appears twice on either side
    batch = embeddings.merge(segments, on="id", how="inner", validate="one_to_one")
    if len(batch) != len(embeddings):
        raise ValueError(f"{path.name}: {len(embeddings) - len(batch)} embeddings have no matching document")
    fast_pg_insert(batch[SEGMENT_COLUMNS], CONNECTION, "segment", SEGMENT_COLUMNS)
    inserted += len(batch)
    print(f"inserted {inserted:,} / {len(segments):,} segments ({time.time() - start:.0f}s)")

if inserted != len(segments):
    raise ValueError(f"{len(segments) - inserted} documents have no embedding")
