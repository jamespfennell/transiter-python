import unittest
import unittest.mock as mock

from transiter import models, exceptions
from transiter.services import stopservice, links
from .. import testutil

import datetime


class TestTripStopTimeFilter(testutil.TestCase(stopservice)):

    TIME_1 = datetime.datetime(4, 4, 4, 4, 10, 0)
    TIME_2 = datetime.datetime(4, 4, 4, 4, 15, 0)
    TIME_3 = datetime.datetime(4, 4, 4, 4, 20, 0)
    TIME_4 = datetime.datetime(4, 4, 4, 4, 25, 0)
    DIRECTION = "Left"

    def setUp(self):
        self.time = self.mockImportedModule(stopservice.time)

    def test_old_trips__exclude(self):

        stop_time = models.TripStopTime(arrival_time=self.TIME_1)
        self.time.time.return_value = self.TIME_4.timestamp()

        stop_time_filter = stopservice._TripStopTimeFilter(0, 10, 0)

        self.assertTrue(stop_time_filter.remove(stop_time, self.DIRECTION))

    def test_old_trips__include_when_no_lower_bound(self):
        stop_time = models.TripStopTime(arrival_time=self.TIME_1)
        self.time.time.return_value = self.TIME_4.timestamp()

        stop_time_filter = stopservice._TripStopTimeFilter(None, 10, 0)

        self.assertFalse(stop_time_filter.remove(stop_time, self.DIRECTION))

    def test_old_trips__include_selectively(self):

        stop_times = [
            models.TripStopTime(arrival_time=self.TIME_1),
            models.TripStopTime(arrival_time=self.TIME_2),
        ]
        self.time.time.return_value = self.TIME_3.timestamp()

        stop_time_filter = stopservice._TripStopTimeFilter(7.5, 10, 0)

        self.assertTrue(stop_time_filter.remove(stop_times[0], self.DIRECTION))
        self.assertFalse(stop_time_filter.remove(stop_times[1], self.DIRECTION))

    def test_direction(self):

        stop_times = [
            models.TripStopTime(arrival_time=self.TIME_2),
            models.TripStopTime(arrival_time=self.TIME_3),
        ]
        self.time.time.return_value = self.TIME_1.timestamp()

        stop_time_filter = stopservice._TripStopTimeFilter(0, 0, 1)

        self.assertFalse(stop_time_filter.remove(stop_times[0], self.DIRECTION))
        self.assertTrue(stop_time_filter.remove(stop_times[1], self.DIRECTION))


class TestDirectionNamesMatcher(unittest.TestCase):
    STOP_PK = 1
    DIRECTION_NAME = "Direction Name"

    def setUp(self):
        self.stop = models.Stop()
        self.stop.pk = self.STOP_PK

        self.stop_event = models.TripStopTime()
        self.stop_event.track = None
        self.stop_event.stop_id_alias = None
        self.stop_event.trip = models.Trip()
        self.stop_event.trip.direction_id = None
        self.stop_event.stop = self.stop

        self.rule = models.DirectionRule()
        self.rule.stop_pk = self.STOP_PK
        self.rule.direction_id = None
        self.rule.track = None
        self.rule.name = self.DIRECTION_NAME

    def test_all_names(self):
        """[Stop service] List all names in direction name matcher"""
        dnm = stopservice._DirectionNameMatcher([self.rule])

        self.assertEqual({self.DIRECTION_NAME}, dnm.all_names())

    def test_no_matching_stop_pk(self):
        """[Stop service] Direction matcher, no match"""
        self.rule.stop_pk = 2
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_direction_id(self):
        """[Stop service] Direction matcher, no matching direction ID"""
        self.rule.direction_id = True
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_track(self):
        """[Stop service] Direction matcher, no matching track"""
        self.rule.track = "Track"
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop_event)

        self.assertEqual(direction_name, None)

    def test_match(self):
        """[Stop service] Direction matcher, match"""
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop_event)

        self.assertEqual(direction_name, self.DIRECTION_NAME)


class TestStopService(testutil.TestCase(stopservice), unittest.TestCase):
    SYSTEM_ID = "1"
    STOP_ONE_ID = "2"
    STOP_ONE_PK = 3
    TRIP_PK = 100
    TRIP_ID = "101"
    ROUTE_ID = "103"
    STOP_TWO_ID = "102"
    DIRECTION_NAME = "Uptown"
    TRIP_STOP_TIME_ONE_PK = 201
    TRIP_STOP_TIME_TWO_PK = 202

    def setUp(self):
        self.stop_dao = self.mockImportedModule(stopservice.stopdam)
        self.systemdam = self.mockImportedModule(stopservice.systemdam)
        self.tripdam = self.mockImportedModule(stopservice.tripdam)
        self.servicepatternmanager = self.mockImportedModule(
            stopservice.servicemapmanager
        )

        self.stop_one = models.Stop()
        self.stop_one.pk = self.STOP_ONE_PK
        self.stop_one.id = self.STOP_ONE_ID

    def test_list_all_in_system(self):
        """[Stop service] List all in system"""
        self.stop_dao.list_all_in_system.return_value = [self.stop_one]

        expected = [
            {"href": links.StopEntityLink(self.stop_one), **self.stop_one.short_repr()}
        ]

        actual = stopservice.list_all_in_system(self.SYSTEM_ID, True)

        self.assertListEqual(actual, expected)
        self.stop_dao.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    def test_list_all_in_system__system_not_found(self):
        """[Stop service] List all in system - system not found"""
        self.systemdam.get_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: stopservice.list_all_in_system(self.SYSTEM_ID),
        )

    def test_get_in_system_by_id__stop_not_found(self):
        """[Stop service] Get stop - stop not found"""
        self.stop_dao.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: stopservice.get_in_system_by_id(self.SYSTEM_ID, self.STOP_ONE_ID),
        )

    @mock.patch.object(stopservice, "_DirectionNameMatcher")
    @mock.patch.object(stopservice, "_build_trip_stop_time_response")
    @mock.patch.object(stopservice, "_build_stop_tree_response")
    def test_get_in_system_by_id(
        self,
        _build_stop_tree_response,
        _build_trip_stop_time_response,
        _DirectionNameMatcher,
    ):
        """[Stop service] Get stop"""

        fake_stop_tree_response = {"id": self.STOP_ONE_ID}
        fake_trip_stop_time_response = {"id": self.TRIP_ID}
        fake_trip_pk_to_last_stop_map = mock.MagicMock()
        fake_service_map_response_map = mock.MagicMock()

        direction_name_matcher = mock.MagicMock()
        _DirectionNameMatcher.return_value = direction_name_matcher
        direction_name_matcher.match.return_value = self.DIRECTION_NAME
        direction_name_matcher.all_names.return_value = [self.DIRECTION_NAME]

        _build_stop_tree_response.return_value = fake_stop_tree_response
        _build_trip_stop_time_response.return_value = fake_trip_stop_time_response

        self.tripdam.get_trip_pk_to_last_stop_map.return_value = (
            fake_trip_pk_to_last_stop_map
        )
        self.servicepatternmanager.build_stop_pk_to_service_maps_response = (
            fake_service_map_response_map
        )

        stop_time_one = models.TripStopTime()
        stop_time_one.pk = self.TRIP_STOP_TIME_ONE_PK
        stop_time_two = models.TripStopTime()
        stop_time_two.pk = self.TRIP_STOP_TIME_TWO_PK
        self.stop_dao.list_stop_time_updates_at_stops.return_value = [
            stop_time_one,
            stop_time_two,
        ]

        stop = self.stop_one
        stop.child_stops = []
        stop.parent_stop = None
        self.stop_dao.get_in_system_by_id.return_value = stop

        expected = {
            **fake_stop_tree_response,
            "directions": [self.DIRECTION_NAME],
            "stop_time_updates": [
                {**fake_trip_stop_time_response},
                {**fake_trip_stop_time_response},
            ],
            "latitude": None,
            "longitude": None,
            "url": None,
            "name": None,
        }

        actual = stopservice.get_in_system_by_id(self.SYSTEM_ID, self.STOP_ONE_ID)

        self.assertDictEqual(expected, actual)

    def test_build_trip_stop_time_response(self):
        """[Stop service] Test build trip stop time response"""
        stop = models.Stop()
        stop.id = self.STOP_ONE_ID
        trip = models.Trip()
        trip.pk = self.TRIP_PK
        trip.id = self.TRIP_ID
        trip_stop_time = models.TripStopTime()
        trip_stop_time.trip = trip
        trip_stop_time.stop = stop
        route = models.Route()
        route.id = self.ROUTE_ID
        trip.route = route
        last_stop = models.Stop()
        last_stop.id = self.STOP_TWO_ID

        expected = {
            "stop_id": self.STOP_ONE_ID,
            "direction": self.DIRECTION_NAME,
            **trip_stop_time.short_repr(),
            "trip": {
                **trip.long_repr(),
                "href": links.TripEntityLink(trip),
                "route": {"href": links.RouteEntityLink(route), **route.short_repr()},
                "last_stop": {
                    **last_stop.short_repr(),
                    "href": links.StopEntityLink(last_stop),
                },
            },
        }

        actual = stopservice._build_trip_stop_time_response(
            trip_stop_time, self.DIRECTION_NAME, {trip.pk: last_stop}, True
        )

        self.maxDiff = None
        self.assertDictEqual(expected, actual)

    def test_build_stop_tree_response(self):
        """[Stop service] Build stop tree response"""
        # Stops tree in this test:
        #     0
        #    / \
        #   1   2
        #  /
        # 3*
        # * not a station
        stops = [models.Stop()] * 4
        for i in range(4):
            stops[i] = models.Stop()
            stops[i].pk = i
            stops[i].id = str(i)
            stops[i].is_station = True
            stops[i].system_id = "system"
        stops[0].child_stops = [stops[1], stops[2]]
        stops[1].child_stops = [stops[3]]
        stops[3].is_station = False

        stop_pk_to_service_maps_response = {pk: pk for pk in range(4)}

        expected = {
            **stops[1].short_repr(),
            "service_maps": 1,
            "href": links.StopEntityLink(stops[1]),
            "parent_stop": {
                **stops[0].short_repr(),
                "service_maps": 0,
                "href": links.StopEntityLink(stops[0]),
                "parent_stop": None,
                "child_stops": [
                    {
                        **stops[2].short_repr(),
                        "service_maps": 2,
                        "href": links.StopEntityLink(stops[2]),
                        "child_stops": [],
                    }
                ],
            },
            "child_stops": [],
        }

        actual = stopservice._build_stop_tree_response(
            stops[1], stop_pk_to_service_maps_response, True, True
        )

        self.maxDiff = None
        self.assertDictEqual(expected, actual)

    def test_get_stop_descendants(self):
        """[Stop service] Get all stop descendants"""
        # Stops tree in this test:
        #     0
        #    / \
        #   1   2
        #  /
        # 3*
        # * not a station
        stops = [models.Stop()] * 4
        for i in range(4):
            stops[i] = models.Stop()
            stops[i].pk = i
            stops[i].id = str(i)
            stops[i].is_station = True
        stops[0].child_stops = [stops[1], stops[2]]
        stops[1].child_stops = [stops[3]]
        stops[3].is_station = False

        expected_pks = {0, 1, 2, 3}

        actual_pks = {stop.pk for stop in stopservice._get_stop_descendants(stops[0])}

        self.assertEqual(expected_pks, actual_pks)

    def test_get_stop_ancestors(self):
        """[Stop service] Get all stop ancestors and ancestor siblings that are stations"""
        # Stops tree in this test:
        #      2
        #    / | \
        #   1  3  4
        #  /   |
        # 0    5*
        # * not a station
        stops = [None] * 6
        for i in range(6):
            stops[i] = models.Stop()
            stops[i].pk = i
            stops[i].id = str(i)
            stops[i].is_station = True
        stops[0].parent_stop = stops[1]
        stops[1].parent_stop = stops[2]
        stops[2].child_stops = [stops[1], stops[3], stops[4]]
        stops[3].child_stops = [stops[5]]
        stops[4].is_station = False

        expected_pks = {0, 1, 2, 3, 5}

        for stop in stops:
            if not stop.is_station:
                continue
            actual_pks = {stop.pk for stop in stopservice._get_all_stations(stop)}

            self.assertEqual(expected_pks, actual_pks)
