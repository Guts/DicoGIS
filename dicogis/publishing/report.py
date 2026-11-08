#! python3  # noqa: E265

"""Outcome of a publication, whatever the catalog."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
from dataclasses import dataclass, field


# ############################################################################
# ########## Classes ###############
# ##################################


@dataclass
class PublishReport:
    """Outcome of a publication run.

    Attributes:
        published: files sent to the catalog
        ignored: files left out: not from DicoGIS, or already published
        failed: files whose publication failed
        up_to_date: files with nothing to add to their record in the catalog
        errors: error messages
        added_fields: names of the fields added to a record of the catalog, by file
        canceled: the run was interrupted, the counters tell what was done until then
    """

    published: int = 0
    ignored: int = 0
    failed: int = 0
    up_to_date: int = 0
    errors: list[str] = field(default_factory=list)
    added_fields: dict[str, list[str]] = field(default_factory=dict)
    canceled: bool = False

    @property
    def total(self) -> int:
        """Total number of files examined."""
        return self.published + self.ignored + self.failed + self.up_to_date
