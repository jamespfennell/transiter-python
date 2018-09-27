from .data import dbconnection
from .data import dbschema
import sqlalchemy

from .services import systemservice


def create_database():
    engine = sqlalchemy.create_engine("postgres://james@/postgres")
    conn = engine.connect()
    try:
        conn.execute("commit")
        conn.execute("DROP DATABASE realtimerail")
    except sqlalchemy.exc.ProgrammingError:
        pass
    conn.execute("commit")
    conn.execute("CREATE DATABASE realtimerail")
    conn.close()

def create_tables():
    dbschema.Base.metadata.create_all(dbconnection.engine)


if(__name__=='__main__'):
    create_database()
    create_tables()
    systemservice.install('nycsubway')
