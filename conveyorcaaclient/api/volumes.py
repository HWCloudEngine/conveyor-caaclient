class VolumeApiMixin(object):
    def list_volume(self, timeout=10):
        params = {'t': timeout}
        url = self._url("/volumes")
        return self._result(self._get(url, params=params), True)

    def get_all_volume_types(self, timeout=10):
        params = {'t': timeout}
        url = self._url("/types")
        return self._result(self._get(url, params=params), True)
