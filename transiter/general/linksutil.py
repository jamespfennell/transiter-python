import flask


class Link:

    endpoint = None
    kwargs = {}

    def url(self):
        if self.endpoint is None or self.kwargs is None:
            raise NotImplementedError
        return flask.url_for(self.endpoint, _external=True, **self.kwargs)


class AboutLink(Link):
    endpoint = 'about'


class SystemsIndexLink(Link):
    endpoint = 'system_endpoints.list_all'


class FeedEntityLink(Link):
    endpoint = 'feed_endpoints.get_in_system_by_id'

    def __init__(self, feed):
        self.kwargs = {
            'system_id': feed.system_id,
            'feed_id': feed.id
        }


class FeedEntityUpdatesLink(Link):
    endpoint = 'feed_endpoints.list_updates_in_feed'

    def __init__(self, feed):
        self.kwargs = {
            'system_id': feed.system_id,
            'feed_id': feed.id
        }


class FeedsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'feed_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class StopEntityLink(Link):

    def __init__(self, stop):
        self.endpoint = 'stop_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': stop.system_id,
            'stop_id': stop.id
        }


class StopsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'stop_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class SystemEntityLink(Link):

    def __init__(self, system):
        self.endpoint = 'system_endpoints.get_by_id'
        self.kwargs = {
            'system_id': system.id,
        }


class RouteEntityLink(Link):

    def __init__(self, route):
        self.endpoint = 'route_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': route.system_id,
            'route_id': route.id
        }


class RoutesInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'route_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class TripEntityLink(Link):

    def __init__(self, trip):
        self.endpoint = 'trip_endpoints.get_in_route_by_id'
        self.kwargs = {
            'system_id': trip.route.system_id,
            'route_id': trip.route.id,
            'trip_id': trip.id
        }

