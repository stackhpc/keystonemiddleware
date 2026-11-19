# Copyright 2019 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystonemiddleware.auth_token import _path_matches
from keystonemiddleware.tests.unit import utils


class TestAccessRules(utils.BaseTestCase):

    def test_path_matches(self):
        good_matches = [
            ('/v2/servers', '/v2/servers'),
            ('/v2/servers/123', '/v2/servers/{server_id}'),
            ('/v2/servers/123/', '/v2/servers/{server_id}/'),
            ('/v2/servers/123', '/v2/servers/*'),
            ('/v2/servers/123/', '/v2/servers/*/'),
            ('/v2/servers/123', '/v2/servers/**'),
            ('/v2/servers/123/', '/v2/servers/**'),
            ('/v2/servers/123/456', '/v2/servers/**'),
            ('/v2/servers', '**'),
            ('/v2/servers/', '**'),
            ('/v2/servers/123', '**'),
            ('/v2/servers/123/456', '**'),
            ('/v2/servers/123/volume/456', '**'),
            ('/v2/servers/123/456', '/v2/*/*/*'),
            ('/v2/123/servers/466', '/v2/{project_id}/servers/{server_id}'),
            # Literal '.' in documented-style OpenStack paths
            ("/v2.1/servers", "/v2.1/servers"),
            ("/v2.1/servers/123/ips", "/v2.1/servers/*/ips"),
            ("/v2.1/servers/123/ips", "/v2.1/servers/{server_id}/ips"),
            ("/v2.1/foo/bar", "/v2.1/**"),
        ]
        for (request, pattern) in good_matches:
            self.assertIsNotNone(_path_matches(request, pattern))
        bad_matches = [
            ('/v2/servers/someuuid', '/v2/servers'),
            ('/v2/servers//', '/v2/servers/{server_id}'),
            ('/v2/servers/123/', '/v2/servers/{server_id}'),
            ('/v2/servers/123/456', '/v2/servers/{server_id}'),
            ('/v2/servers/123/456', '/v2/servers/*'),
            ('/v2/servers', 'v2/servers'),
            ('/v2/servers/123/456/789', '/v2/*/*/*'),
            ('/v2/servers/123/', '/v2/*/*/*'),
            ('/v2/servers/', '/v2/servers/{server_id}'),
            ('/v2/servers', '/v2/servers/{server_id}'),
            # Regex metacharacters in the pattern are literals, not regex
            ("/v2X1/servers", "/v2.1/servers"),
            ("/healthAcheck", "/health.check"),
            ("/api/v1", "/api/v1+"),
            ("/api/v1ABC", "/api/v1+"),
            ("/users/id/profile", "/users/(id)/profile"),
        ]
        for (request, pattern) in bad_matches:
            self.assertIsNone(_path_matches(request, pattern))

    def test_path_matches_literal_metacharacters(self):
        # Patterns that look like regex still only match themselves.
        self.assertIsNotNone(_path_matches("/health.check", "/health.check"))
        self.assertIsNotNone(_path_matches("/api/v1+", "/api/v1+"))
        self.assertIsNotNone(
            _path_matches("/users/(id)/profile", "/users/(id)/profile")
        )
        nested = "/((((((((((.+)+)+)+)+)+)+)+)+)+)!"
        self.assertIsNotNone(_path_matches(nested, nested))

    def test_path_matches_nested_quantifiers_not_redos(self):
        # Before the fix this pattern caused catastrophic backtracking, so
        # a long non-matching request would effectively never return.
        pattern = "/((((((((((.+)+)+)+)+)+)+)+)+)+)!"
        request = "/" + ("a" * 30)
        self.assertIsNone(_path_matches(request, pattern))
