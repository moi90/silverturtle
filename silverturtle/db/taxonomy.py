from dataclasses import dataclass
from typing import List, Optional, Tuple, Type

import sqlalchemy.engine.base
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import select
from sqlalchemy.sql import exists
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.sqltypes import ARRAY, Boolean, String

from .models import NodeID, objects

from sqlalchemy.orm import declarative_base, deferred, relationship
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy.orm import object_session
from sqlalchemy import ForeignKey

Base: Type = declarative_base()


class Taxon(Base):
    __tablename__ = "taxons"
    id = Column(UUIDType(), primary_key=True)
    parent_id = Column(ForeignKey("taxons.id"))

    @classmethod
    def root(cls, session: Session) -> "Taxon":
        return session.query(Taxon).filter(Taxon.parent_id == None).one()

    def hull(self, id_only=True) -> List:
        session: Session = object_session(self)  # type: ignore
        session.query(Taxon)


class CUBE:
    pass


@dataclass
class Tag:
    values: Tuple[str]
    reject: bool


class ObjectTag(Base):
    object_id = Column(ForeignKey("objects.id"))
    tag = Column(ARRAY(String))
    reject = Column(Boolean)

    def as_tag(self):
        return Tag(tuple(self.tag), self.reject)  # type: ignore


class Object(base):  # type: ignore
    __tablename__ = "objects"

    taxon_id = Column(ForeignKey("taxons.id"))
    vector = deferred(Column(CUBE))
    tags = relationship("ObjectTag")


@dataclass
class Concept:
    taxon: Optional[Taxon]
    taxons_reject: Optional[List[Taxon]]
    tags: Optional[List[Tag]]

    @classmethod
    def find(cls, id_string: str, session: Session):
        ...

    @classmethod
    def from_json(cls, data, session: Session):
        ...

    def query_extension(self, session: Session):
        query = session.query(Object)

        # Restrict to hull of taxon
        if self.taxon is not None:
            query = query.filter(Object.taxon_id.in_(self.taxon.hull()))

        # Exclude hulls of rejected taxons
        if self.taxons_reject is not None:
            for t in self.taxons_reject:
                query = query.filter(~Object.taxon_id.in_(t.hull()))

        # Restrict to tagged
        if self.tags is not None:
            for tag in self.tags:
                if tag.reject:
                    stmt = (
                        ~exists()
                        .where(ObjectTag.tag.between(tag.values, tag.values + (None,)))
                        .where(~ObjectTag.reject)
                    )
                else:
                    stmt = (
                        exists()
                        .where(ObjectTag.tag.between(tag.values, tag.values + (None,)))
                        .where(~ObjectTag.reject)
                    )
                query = query.filter(stmt)

        return query
