from ..utils import jsonutil
from decorator import decorator
from ..data import dbexceptions


HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_404_NOT_FOUND = 404


def _process_request(callback, func, *args, **kw):
    try:
        result = func(*args, **kw)
    except dbexceptions.IdNotFoundError:
        return '', HTTP_404_NOT_FOUND
    #except Exception as e:
    #    return str(e), 500

    return callback(result)


def _post_process_get(result):
    return jsonutil.convert_for_http(result), HTTP_200_OK


def _post_process_put(result):
    # NOTE(fennell): put services return true if the resource was
    # created and false otherwise
    if result:
        return '', HTTP_201_CREATED
    else:
        return '', HTTP_204_NO_CONTENT


def _post_process_delete(result):
    return '', HTTP_204_NO_CONTENT


@decorator
def http_get_response(func, *args, **kw):
    return _process_request(_post_process_get, func, *args, **kw)


@decorator
def http_put_response(func, *args, **kw):
    return _process_request(_post_process_put, func, *args, **kw)


@decorator
def http_delete_response(func, *args, **kw):
    return _process_request(_post_process_delete, func, *args, **kw)



