from transiter.data import database
from transiter import models
import sqlalchemy.sql.expression as sql
from sqlalchemy import func
from sqlalchemy import orm


def get_default_routes_at_stops_map(stop_pks):
    session = database.get_session()
    query = (
        session.query(
            models.ServiceMapGroup.id,
            models.ServicePatternVertex.stop_pk,
            models.Route
        )
        .join(
            models.ServicePattern,
            models.ServicePattern.group_pk == models.ServiceMapGroup.pk
        )
        .join(
            models.ServicePatternVertex,
            models.ServicePatternVertex.service_pattern_pk == models.ServicePattern.pk
        )
        .join(
            models.Route,
            models.Route.pk == models.ServicePattern.route_pk
        )
        .filter(models.ServicePatternVertex.stop_pk.in_(stop_pks))
        .filter(models.ServiceMapGroup.use_for_routes_at_stop)
    )
    print(query)

    response = {stop_pk: {} for stop_pk in stop_pks}
    for group_id, stop_pk, route in query:
        if group_id not in response[stop_pk]:
            response[stop_pk][group_id] = []
        response[stop_pk][group_id].append(route)
    return response


#TODO stop_pks_map -> paths
def get_scheduled_trip_pk_to_stop_pks_map():
    statement = sql.select(
        [
            models.ScheduledTripStopTime.trip_pk,
            models.ScheduledTripStopTime.stop_pk
        ]
    ).order_by(models.ScheduledTripStopTime.trip_pk, models.ScheduledTripStopTime.stop_sequence)
    session = database.get_session()
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in session.execute(statement):
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    return trip_pk_to_stop_pks


def list_scheduled_trips_with_times_in_system():
    session = database.get_session()
    import time

    first_stop_query = session.query(
        models.ScheduledTripStopTime.trip_pk.label('trip_pk'),
        func.min(models.ScheduledTripStopTime.departure_time).label('time')
    ).group_by(models.ScheduledTripStopTime.trip_pk).subquery()

    last_stop_query = session.query(
        models.ScheduledTripStopTime.trip_pk.label('trip_pk'),
        func.max(models.ScheduledTripStopTime.departure_time).label('time')
    ).group_by(models.ScheduledTripStopTime.trip_pk).subquery()

    query = (
        session.query(
            models.ScheduledTrip,
            first_stop_query.c.time,
            last_stop_query.c.time,
        )
        .join(
            first_stop_query,
            models.ScheduledTrip.pk == first_stop_query.c.trip_pk
        )
        .join(
            last_stop_query,
            models.ScheduledTrip.pk == last_stop_query.c.trip_pk
        )
    )
    for trip, start_time, end_time in query:
        yield trip, start_time, end_time

def list_scheduled_trip_raw_service_maps_in_system(
        system_id=None,
        min_start_time=None,
        max_start_time=None,
        min_end_time=None,
        max_end_time=None,
        sunday=None):

    first_stop_time_stmt = (
        sql.select([func.min(models.ScheduledTripStopTime.stop_sequence)])
        .where(models.ScheduledTripStopTime.trip_pk == models.ScheduledTrip.pk)
        .select_from(models.ScheduledTripStopTime)
        .correlate(models.ScheduledTrip)
    )
    last_stop_time_stmt = (
        sql.select([func.max(models.ScheduledTripStopTime.stop_sequence)])
        .where(models.ScheduledTripStopTime.trip_pk == models.ScheduledTrip.pk)
        .select_from(models.ScheduledTripStopTime)
        .correlate(models.ScheduledTrip)
    )

    first_stop_time = orm.aliased(
        models.ScheduledTripStopTime, name='first_stop_time')
    last_stop_time = orm.aliased(
        models.ScheduledTripStopTime, name='last_stop_time')

    statement = (
        sql.select(
            [models.Route.pk,
             models.ScheduledTrip.raw_service_map_string,
             func.count()]
        )
        .select_from(
            sql.join(models.ScheduledService, models.ScheduledTrip)
            .join(models.Route)
            .join(
                first_stop_time,
                sql.and_(
                        first_stop_time.trip_pk == models.ScheduledTrip.pk,
                        first_stop_time.stop_sequence == first_stop_time_stmt
                )
            )
            .join(
                last_stop_time,
                sql.and_(
                    last_stop_time.trip_pk == models.ScheduledTrip.pk,
                    last_stop_time.stop_sequence == last_stop_time_stmt
                )
            )
        )
    )
    if system_id is not None:
        statement = statement.where(models.Route.system_id == system_id)
    if sunday is not None:
        statement = statement.where(models.ScheduledService.sunday == sunday)

    if min_start_time is not None:
        statement = statement.where(
            first_stop_time.departure_time > min_start_time)
    if max_start_time is not None:
        statement = statement.where(
            first_stop_time.departure_time < max_start_time)
    if min_end_time is not None:
        statement = statement.where(
            last_stop_time.arrival_time > min_end_time)
    if max_start_time is not None:
        statement = statement.where(
            last_stop_time.arrival_time < max_end_time)

    statement = statement.group_by(
        models.Route.pk, models.ScheduledTrip.raw_service_map_string
    )
    import json

    session = database.get_session()
    for route_id, raw_service_map_str, multiplicity in session.execute(statement):
        yield route_id, json.loads(raw_service_map_str), multiplicity
