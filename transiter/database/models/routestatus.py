from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class RouteStatus(Base):
    __tablename__ = 'route_status'

    id = Column(Integer, primary_key=True)
    status_id = Column(String)
    status_type = Column(String)
    status_priority = Column(Integer)
    message_title = Column(String)
    message_content = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

    routes = relationship("Route", secondary="route_status_routes")

    def short_repr(self):
        return {
            'status_type': self.status_type,
            'message_title': self.message_title,
            'message_content': self.message_content,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'creation_time': self.creation_time,
        }


route_status_routes = Table(
    'route_status_routes', Base.metadata,
    Column('route_status_pri_key', Integer, ForeignKey("route_status.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)