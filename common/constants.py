"""Constants shared by several apps."""

GENDER_CHOICES = [
    ("Female", "Female"),
    ("Male", "Male"),
]

GENDER_FEMALE = "Female"
GENDER_MALE = "Male"

# Historical storage prefix. Every model that carried a table under the original
# single-app layout keeps that name via `Meta.db_table` so existing rows survive
# the split into per-domain apps untouched. These constants document where the
# names come from and give a single place to change later.
LEGACY_TABLE_PREFIX = "cab_g_"
