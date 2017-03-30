# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2010 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


class ComputeApiMixin(object):
    def list_instances(self, timeout=10):
        params = {'t': timeout}
        url = self._url("/server/list")
        return self._result(self._get(url, params=params), True)

    def attach_volume(self, volume_id, server_id, device, timeout=10):
        params = {'t': timeout}
        url = self._url("/server/attach-volume/" + server_id)
        res = self._post_json(url, params=params,
                              data={'volumeId': volume_id,
                                    'device': device})
        self._raise_for_status(res)
        return res.raw

    def detach_volume(self, volume_id, server_id, timeout=10):
        params = {'t': timeout}
        url = self._url("/server/detach_volume/" + volume_id)
        res = self._post_json(url, params=params,
                              data={'attachment_id': server_id})
        self._raise_for_status(res)
        return res.raw
