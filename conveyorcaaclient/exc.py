"""
Main exceptions def for wormhole client
"""
import re
import requests
import six
import sys


class BaseException(Exception):
    """An error occurred."""

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message or self.__class__.__doc__


class CommandError(BaseException):
    """Invalid usage of CLI."""


class InvalidEndpoint(BaseException):
    """The provided endpoint is invalid."""


class CommunicationError(BaseException):
    """Unable to communicate with server."""


class ClientException(Exception):
    """DEPRECATED!"""


class HTTPException(ClientException):
    """Base exception for all HTTP-derived exceptions."""
    code = 'N/A'

    def __init__(self, details=None):
        self.details = details or self.__class__.__name__

    def __str__(self):
        return "%s (HTTP %s)" % (self.details, self.code)


class HTTPMultipleChoices(HTTPException):
    code = 300

    def __str__(self):
        self.details = ("Requested version of Wormhole API is not "
                        "available.")
        return "%s (HTTP %s) %s" % (self.__class__.__name__, self.code,
                                    self.details)


class BadRequest(HTTPException):
    """DEPRECATED!"""
    code = 400


class HTTPBadRequest(BadRequest):
    pass


class Unauthorized(HTTPException):
    """DEPRECATED!"""
    code = 401


class HTTPUnauthorized(Unauthorized):
    pass


class Forbidden(HTTPException):
    """DEPRECATED!"""
    code = 403


class HTTPForbidden(Forbidden):
    pass


class NotFound(HTTPException):
    """DEPRECATED!"""
    code = 404


class HTTPNotFound(NotFound):
    pass


class HTTPMethodNotAllowed(HTTPException):
    code = 405


class Conflict(HTTPException):
    """DEPRECATED!"""
    code = 409


class HTTPConflict(Conflict):
    pass


class OverLimit(HTTPException):
    """DEPRECATED!"""
    code = 413


class HTTPOverLimit(OverLimit):
    pass


class HTTPInternalServerError(HTTPException):
    code = 500


class HTTPNotImplemented(HTTPException):
    code = 501


class HTTPBadGateway(HTTPException):
    code = 502


class ServiceUnavailable(HTTPException):
    """DEPRECATED!"""
    code = 503


class HTTPServiceUnavailable(ServiceUnavailable):
    pass


# NOTE(bcwaldon): Build a mapping of HTTP codes to corresponding exception
# classes
_code_map = {}
for obj_name in dir(sys.modules[__name__]):
    if obj_name.startswith('HTTP'):
        obj = getattr(sys.modules[__name__], obj_name)
        _code_map[obj.code] = obj


def from_response(response, body=None):
    """Return an instance of an HTTPException based on httplib response."""
    cls = _code_map.get(response.status_code, HTTPException)
    if body and 'json' in response.headers['content-type']:
        # Iterate over the nested objects and retrieve the "message"attribute.
        messages = [obj.get('message') for obj in response.json().values()]
        # Join all of the messages together nicely and filter out any objects
        # that don't have a "message" attr.
        details = '\n'.join(i for i in messages if i is not None)
        return cls(details=details)
    elif body and 'html' in response.headers['content-type']:
        # Split the lines, strip whitespace and inline HTML from the response.
        details = [re.sub(r'<.+?>', '', i.strip())
                   for i in response.text.splitlines()]
        details = [i for i in details if i]
        # Remove duplicates from the list.
        details_seen = set()
        details_temp = []
        for i in details:
            if i not in details_seen:
                details_temp.append(i)
                details_seen.add(i)
        # Return joined string separated by colons.
        details = ': '.join(details_temp)
        return cls(details=details)
    elif body:
        if six.PY3:
            body = body.decode('utf-8')
        details = body.replace('\n\n', '\n')
        return cls(details=details)

    return cls()


class NoTokenLookupException(Exception):
    """DEPRECATED!"""
    pass


class EndpointNotFound(Exception):
    """DEPRECATED!"""
    pass


class SSLConfigurationError(BaseException):
    pass


class SSLCertificateError(BaseException):
    pass


class InvalidHost(BaseException):
    pass


class APIError(requests.exceptions.HTTPError):
    def __init__(self, message, response, explanation=None):
        # requests 1.2 supports response as a keyword argument, but
        # requests 1.1 doesn't
        super(APIError, self).__init__(message)
        self.response = response

        self.explanation = explanation

        if self.explanation is None and response.content:
            self.explanation = response.content.strip()

    def __str__(self):
        message = super(APIError, self).__str__()

        if self.is_client_error():
            message = '{0} Client Error: {1}'.format(
                self.response.status_code, self.response.reason)

        elif self.is_server_error():
            message = '{0} Server Error: {1}'.format(
                self.response.status_code, self.response.reason)

        if self.explanation:
            message = '{0} ("{1}")'.format(message, self.explanation)

        return message

    def is_client_error(self):
        return 400 <= self.response.status_code < 500

    def is_server_error(self):
        return 500 <= self.response.status_code < 600
