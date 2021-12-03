from typing import Any, NewType
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

metadata = MetaData()

NodeID = NewType("NodeID", Any)

objects = Table("objects", metadata, Column("object_id", String, primary_key=True))
