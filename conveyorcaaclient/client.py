import json

import requests
import six
import socket

from conveyorcaaclient.api import compute
from conveyorcaaclient.api import version
from conveyorcaaclient.api import volumes
from conveyorcaaclient import constants
from conveyorcaaclient import exc
from conveyorcaaclient.utils import utils


class Client(requests.Session,
             version.VersionApiMixin,
             compute.ComputeApiMixin,
             volumes.VolumeApiMixin):
    def __init__(self, host_ip, port=7127, scheme="http", version=None,
                 timeout=constants.DEFAULT_TIMEOUT_SECONDS,
                 proxies={"http": None, "https": None}):
        super(Client, self).__init__()

        if not host_ip:
            raise exc.InvalidHost(
                'The host argument must be provided.'
            )

        self.proxies = proxies

        self.timeout = timeout
        base_url = utils.parse_host(host_ip, port, scheme)
        self.base_url = base_url

        # version detection needs to be after unix adapter mounting
        if version is None:
            self._version = constants.DEFAULT_HYPERVM_API_VERSION
        elif isinstance(version, six.string_types):
            self._version = version
        else:
            raise exc.BaseException(
                'Version parameter must be a string or None.Found {0}'.format(
                    type(version).__name__
                )
            )

    def _set_request_timeout(self, kwargs):
        """Prepare the kwargs for an HTTP request by inserting the timeout
        parameter, if not already present.
        """

        kwargs.setdefault('timeout', self.timeout)
        return kwargs

    def _head(self, url, **kwargs):
        return self._request('HEAD', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _get(self, url, **kwargs):
        return self._request('GET', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _post(self, url, **kwargs):
        return self._request('POST', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _put(self, url, **kwargs):
        return self._request('PUT', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _patch(self, url, **kwargs):
        return self._request('PATCH', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _delete(self, url, **kwargs):
        return self._request('DELETE', url, proxies=self.proxies,
                             **self._set_request_timeout(kwargs))

    def _url(self, pathfmt, *args, **kwargs):
        for arg in args:
            if not isinstance(arg, six.string_types):
                raise ValueError(
                    'Expected a string but found {0} ({1}) '
                    'instead'.format(arg, type(arg))
                )

        args = map(six.moves.urllib.parse.quote_plus, args)

        if kwargs.get('versioned_api', True):
            return '{0}/v{1}{2}'.format(
                self.base_url, self._version, pathfmt.format(*args)
            )
        else:
            return '{0}{1}'.format(self.base_url, pathfmt.format(*args))

    def _raise_for_status(self, response, explanation=None):
        """Raises wormhole exceptions."""
        if not response.ok:
            raise exc.from_response(response, response.content)
        elif (response.status_code == requests.codes.MULTIPLE_CHOICES and
                      response.request.path_url != '/versions'):
            raise exc.from_response(response)

    def _result(self, response, json=False, binary=False):
        assert not (json and binary)
        self._raise_for_status(response)

        if json:
            return response.json()
        if binary:
            return response.content
        return response.text

    def _post_json(self, url, data, **kwargs):
        # Go <1.1 can't unserialize null to a string
        # so we do this disgusting thing here.
        data2 = {}
        if data is not None:
            for k, v in six.iteritems(data):
                if v is not None:
                    data2[k] = v

        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Content-Type'] = 'application/json'
        return self._post(url, data=json.dumps(data2), **kwargs)

    def _attach_params(self, override=None):
        return override or {
            'stdout': 1,
            'stderr': 1,
            'stream': 1
        }

    def _get_result(self, container, stream, res):
        cont = self.inspect_container(container)
        return self._get_result_tty(stream, res, cont['Config']['Tty'])

    def get_adapter(self, url):
        try:
            return super(Client, self).get_adapter(url)
        except requests.exceptions.InvalidSchema as e:
            if self._custom_adapter:
                return self._custom_adapter
            else:
                raise e

    @property
    def api_version(self):
        return self._version

    def _request(self, method, url, **kwargs):
        """Send an http request with the specified characteristics.

        Wrapper around httplib.HTTP(S)Connection.request to handle tasks such
        as setting headers and error handling.
        """
        try:
            resp = self.request(method,
                                url,
                                **kwargs)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError, socket.gaierror,
                socket.error, socket.timeout) as e:
            message = ("Error communicating with %(url)s: %(e)s" %
                       dict(url=url, e=e))
            raise exc.CommunicationError(message=message)

        return resp
