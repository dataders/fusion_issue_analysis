import unittest
from unittest.mock import patch

import requests as raw_requests

from extract.github import helpers


class FakeGraphqlResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return {
            "data": {
                "repository": {"issues": {"nodes": [], "pageInfo": {"endCursor": None}}},
                "rateLimit": {"cost": 1, "remaining": 4999},
            }
        }


class GithubHelpersTests(unittest.TestCase):
    def test_graphql_query_retries_chunked_response_failures(self) -> None:
        with (
            patch.object(
                raw_requests,
                "post",
                side_effect=[
                    raw_requests.exceptions.ChunkedEncodingError(
                        "Response ended prematurely"
                    ),
                    FakeGraphqlResponse(),
                ],
            ) as post,
            patch.object(helpers.time, "sleep") as sleep,
        ):
            data, rate_limit = helpers._run_graphql_query("token", "query", {})

        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once()
        self.assertEqual(rate_limit["remaining"], 4999)
        self.assertIn("repository", data)


if __name__ == "__main__":
    unittest.main()
