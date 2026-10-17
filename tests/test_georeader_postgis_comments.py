#! python3  # noqa: E265


"""
Tests for ReadPostGIS.get_relations_comments() caching, without a database.

Usage from the repo root folder:
    pytest tests/test_georeader_postgis_comments.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import gc
import sys
import weakref
from unittest.mock import MagicMock

# 3rd party
import pytest


pytest.importorskip("osgeo", reason="GDAL (gdal extra) required")

# project
from dicogis.georeaders.read_postgis import ReadPostGIS  # noqa: E402


# ##############################################################################
# ########## Functions #############
# ##################################


def _reader_with_comments(comments: dict[str, str | None]) -> ReadPostGIS:
    """Build a reader whose connection answers the comments query.

    Args:
        comments: "schema.relation" -> comment, None for an uncommented one

    Returns:
        reader with a fake connection counting ExecuteSQL calls
    """
    reader = ReadPostGIS(service="fake")
    rows = [
        {
            "schema_name": name.split(".")[0],
            "relation_name": name.split(".")[1],
            "relation_comment": comment,
        }
        for name, comment in comments.items()
    ]
    reader.conn = MagicMock()
    reader.conn.ExecuteSQL.side_effect = lambda sql: iter(rows)
    return reader


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_comments_are_queried_once_per_reader() -> None:
    reader = _reader_with_comments({"public.parcels": "Cadastre", "public.roads": None})

    first = reader.get_relations_comments()
    second = reader.get_relations_comments()

    assert first == second == {"public.parcels": "Cadastre"}
    reader.conn.ExecuteSQL.assert_called_once()


def test_readers_do_not_share_comments() -> None:
    """Each reader keeps its own comments: one database's comments must not
    be served to a reader of another database."""
    reader_a = _reader_with_comments({"public.parcels": "Database A"})
    reader_b = _reader_with_comments({"public.parcels": "Database B"})

    assert reader_a.get_relations_comments() == {"public.parcels": "Database A"}
    assert reader_b.get_relations_comments() == {"public.parcels": "Database B"}


def test_reader_is_released_once_unused() -> None:
    """The comments cache used to be a class-level lru_cache, keyed by the
    reader: it kept every reader, and its database connection, alive."""
    reader = _reader_with_comments({"public.parcels": "Cadastre"})
    reader.get_relations_comments()
    reader_ref = weakref.ref(reader)

    del reader
    gc.collect()

    assert reader_ref() is None


def test_failed_query_returns_empty_and_is_not_retried() -> None:
    reader = ReadPostGIS(service="fake")
    reader.conn = MagicMock()
    reader.conn.ExecuteSQL.side_effect = RuntimeError("no catalog access")

    assert reader.get_relations_comments() == {}
    assert reader.get_relations_comments() == {}
    reader.conn.ExecuteSQL.assert_called_once()


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
