from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref

from .base import Base
from .updatableentity import UpdatableEntity


class Stop(Base, UpdatableEntity):
    __tablename__ = "stop"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_id = Column(String, ForeignKey("system.id"))  # , nullable=False)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)
    parent_stop_pk = Column(Integer, ForeignKey("stop.pk"), index=True)

    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    latitude = Column(Numeric(precision=9, scale=6))
    is_station = Column(Boolean)

    parent_stop_id = None

    system = relationship("System", back_populates="stops")
    source = relationship("FeedUpdate", cascade="none")
    # NOTE: this relationship is a little tricky and this definition follows
    # https://docs.sqlalchemy.org/en/latest/_modules/examples/adjacency_list/adjacency_list.html
    child_stops = relationship(
        "Stop",
        cascade="none",
        backref=backref("parent_stop", remote_side=pk, cascade="none"),
    )
    direction_name_rules = relationship(
        "DirectionNameRule",
        back_populates="stop",
        cascade="all, delete-orphan",
        order_by="DirectionNameRule.priority",
    )
    trip_times = relationship(
        "TripStopTime", back_populates="stop", cascade="delete, delete-orphan"
    )
    service_pattern_vertices = relationship(
        "ServiceMapVertex", back_populates="stop", cascade="delete, delete-orphan"
    )
    scheduled_trip_times = relationship(
        "ScheduledTripStopTime", back_populates="stop", cascade="delete, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("system_id", "id"),)

    _short_repr_list = [id, name]
