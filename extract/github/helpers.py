import time
from datetime import datetime, timezone
from typing import Iterator, List, Optional, Tuple

from dlt.common.typing import DictStrAny, StrAny
from dlt.common.utils import chunks
from dlt.sources.helpers import requests

from .queries import (
    COMMENT_REACTIONS_QUERY,
    ISSUE_ONLY_FIELDS,
    ISSUES_QUERY,
    MILESTONES_QUERY,
    STARGAZERS_QUERY,
    RATE_LIMIT,
)
from .settings import GRAPHQL_API_BASE_URL, REST_API_BASE_URL

MAX_RETRIES = 5
RETRY_BASE_DELAY = 30  # seconds
RETRY_STATUS_CODES = {403, 429, 500, 502, 503, 504}
REQUEST_TIMEOUT_SECONDS = 60


#
# Shared
#
def _get_auth_header(access_token: Optional[str]) -> StrAny:
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    else:
        # REST API works without access token (with high rate limits)
        return {}


#
# Rest API helpers
#
def get_rest_pages(access_token: Optional[str], query: str) -> Iterator[List[StrAny]]:
    def _request(page_url: str) -> requests.Response:
        r = requests.get(page_url, headers=_get_auth_header(access_token))
        print(
            f"got page {page_url}, requests left: " + r.headers["x-ratelimit-remaining"]
        )
        return r

    next_page_url = REST_API_BASE_URL + query
    while True:
        r: requests.Response = _request(next_page_url)
        page_items = r.json()
        if len(page_items) == 0:
            break
        yield page_items
        if "next" not in r.links:
            break
        next_page_url = r.links["next"]["url"]


#
# GraphQL API helpers
#
def get_stargazers(
    owner: str,
    name: str,
    access_token: str,
    items_per_page: int,
    max_items: Optional[int],
) -> Iterator[Iterator[StrAny]]:
    variables = {"owner": owner, "name": name, "items_per_page": items_per_page}
    for page_items in _get_graphql_pages(
        access_token, STARGAZERS_QUERY, variables, "stargazers", max_items
    ):
        yield map(
            lambda item: {"starredAt": item["starredAt"], "user": item["node"]},
            page_items,
        )


def get_milestones(
    owner: str,
    name: str,
    access_token: str,
    items_per_page: int,
    max_items: Optional[int],
) -> Iterator[List[StrAny]]:
    variables = {"owner": owner, "name": name, "items_per_page": items_per_page}
    for page_items in _get_graphql_pages(
        access_token, MILESTONES_QUERY, variables, "milestones", max_items
    ):
        yield page_items


def get_reactions_data(
    node_type: str,
    owner: str,
    name: str,
    access_token: str,
    items_per_page: int,
    max_items: Optional[int],
    since: Optional[str] = None,
    labels: Optional[List[str]] = None,
    repository: Optional[str] = None,
) -> Iterator[Iterator[StrAny]]:
    variables = {
        "owner": owner,
        "name": name,
        "issues_per_page": items_per_page,
        "first_reactions": 100,
        "first_comments": 100,
        "first_timeline_items": 50,
        "node_type": node_type,
    }
    # `issueType`, `parent`, `stateReason`, `closedByPullRequestsReferences`
    # are only valid on the Issue type; they would cause a GraphQL validation
    # error if included in the pullRequests body.
    # `filterBy: {since, labels}` is also only valid on issues, not pullRequests.
    issue_only_fields = ISSUE_ONLY_FIELDS if node_type == "issues" else ""
    if node_type == "issues":
        filter_parts = []
        extra_var_decls = ", $since: DateTime"
        variables["since"] = since
        filter_parts.append("since: $since")
        if labels:
            extra_var_decls += ", $labels: [String!]"
            variables["labels"] = labels
            filter_parts.append("labels: $labels")
        filterby_clause = f", filterBy: {{{', '.join(filter_parts)}}}"
    else:
        extra_var_decls = ""
        filterby_clause = ""
    query = ISSUES_QUERY % (extra_var_decls, node_type, filterby_clause, issue_only_fields)
    for page_items in _get_graphql_pages(
        access_token, query, variables, node_type, max_items
    ):
        # use reactionGroups to query for reactions to comments that have any reactions. reduces cost by 10-50x
        reacted_comment_ids = {}
        for item in page_items:
            for comment in item["comments"]["nodes"]:
                if any(group["createdAt"] for group in comment["reactionGroups"]):
                    reacted_comment_ids[comment["id"]] = comment
                comment.pop("reactionGroups", None)

        # get comment reactions by querying comment nodes separately
        comment_reactions = _get_comment_reaction(
            list(reacted_comment_ids.keys()), access_token
        )
        # attach the reaction nodes where they should be
        for comment in comment_reactions.values():
            comment_id = comment["id"]
            reacted_comment_ids[comment_id]["reactions"] = comment["reactions"]

        def _enrich(item: DictStrAny) -> DictStrAny:
            item = _extract_nested_nodes(item)
            if repository:
                item["repository"] = repository
            return item

        yield map(_enrich, page_items)


def _extract_top_connection(data: StrAny, node_type: str) -> StrAny:
    assert (
        isinstance(data, dict) and len(data) == 1
    ), f"The data with list of {node_type} must be a dictionary and contain only one element"
    data = next(iter(data.values()))
    return data[node_type]  # type: ignore


def _extract_nested_nodes(item: DictStrAny) -> DictStrAny:
    """Recursively moves `nodes` and `totalCount` to reduce nesting."""
    item["reactions_totalCount"] = item["reactions"].get("totalCount", 0)
    item["reactions"] = item["reactions"]["nodes"]
    comments = item["comments"]
    item["comments_totalCount"] = item["comments"].get("totalCount", 0)
    for comment in comments["nodes"]:
        if "reactions" in comment:
            comment["reactions_totalCount"] = comment["reactions"].get("totalCount", 0)
            comment["reactions"] = comment["reactions"]["nodes"]
    item["comments"] = comments["nodes"]
    if "timelineItems" in item:
        timeline = item["timelineItems"]
        item["timeline_items_totalCount"] = timeline.get("totalCount", 0)
        item["timeline_items"] = timeline["nodes"]
        item.pop("timelineItems", None)
    if "closedByPullRequestsReferences" in item:
        cbpr = item["closedByPullRequestsReferences"]
        item["closed_by_pull_requests_references"] = cbpr.get("nodes", [])
        item.pop("closedByPullRequestsReferences", None)
    return item


def _parse_reset_at(reset_at_str: Optional[str]) -> Optional[float]:
    """Parse a GitHub ISO-8601 resetAt timestamp into a Unix epoch float."""
    if not reset_at_str:
        return None
    try:
        dt = datetime.fromisoformat(reset_at_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError):
        return None


def _run_graphql_query(
    access_token: str, query: str, variables: DictStrAny
) -> Tuple[StrAny, StrAny]:
    import requests as raw_requests

    retryable_errors = (
        raw_requests.exceptions.ChunkedEncodingError,
        raw_requests.exceptions.ConnectionError,
        raw_requests.exceptions.Timeout,
    )

    def _sleep_before_retry(reason: str, retry_number: int, until: Optional[float] = None) -> None:
        if until is not None:
            delay = max(until - time.time(), 0) + 5  # 5s safety margin
        else:
            delay = RETRY_BASE_DELAY * (2 ** (retry_number - 1))
        print(
            f"GitHub GraphQL request failed ({reason}), retrying in {delay:.1f}s "
            f"(attempt {retry_number}/{MAX_RETRIES})"
        )
        time.sleep(delay)

    def _extract_retry_until(r: raw_requests.Response) -> Optional[float]:
        """Return the Unix timestamp to sleep until, from Retry-After or x-ratelimit-reset."""
        retry_after = r.headers.get("Retry-After")
        if retry_after:
            try:
                return time.time() + float(retry_after)
            except ValueError:
                pass
        reset_header = r.headers.get("x-ratelimit-reset")
        if reset_header:
            try:
                return float(reset_header)
            except ValueError:
                pass
        return None

    def _request() -> dict:
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = raw_requests.post(
                    GRAPHQL_API_BASE_URL,
                    json={"query": query, "variables": variables},
                    headers=_get_auth_header(access_token),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                if r.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                    until = _extract_retry_until(r)
                    _sleep_before_retry(f"HTTP {r.status_code}", attempt + 1, until)
                    continue
                r.raise_for_status()
                return r.json()  # inside try so ChunkedEncodingError during body streaming is retried
            except retryable_errors:
                if attempt == MAX_RETRIES:
                    raise
                _sleep_before_retry("network response ended early", attempt + 1)

        raise RuntimeError("GitHub GraphQL request retry loop exhausted")

    data = _request()

    # GitHub GraphQL returns HTTP 200 for RATE_LIMITED errors — handle them here
    # so the retry loop above (which only checks HTTP status codes) can act on them.
    if "errors" in data:
        errors = data["errors"]
        rate_limited = any(
            e.get("type") == "RATE_LIMITED" for e in errors if isinstance(e, dict)
        )
        if rate_limited:
            # Pull resetAt from the partial rateLimit node if present
            reset_at_str = (data.get("data") or {}).get("rateLimit", {}).get("resetAt")
            until = _parse_reset_at(reset_at_str)
            delay = max((until - time.time()), 0) + 5 if until else RETRY_BASE_DELAY
            print(f"GitHub GraphQL RATE_LIMITED — sleeping {delay:.1f}s until resetAt ({reset_at_str})")
            time.sleep(delay)
            # Recurse: _run_graphql_query will do its own retry loop
            return _run_graphql_query(access_token, query, variables)
        raise ValueError(data)

    data = data["data"]
    # pop rate limits
    rate_limit = data.pop("rateLimit", {"cost": 0, "remaining": 0})
    return data, rate_limit


def _get_graphql_pages(
    access_token: str, query: str, variables: DictStrAny, node_type: str, max_items: int
) -> Iterator[List[DictStrAny]]:
    items_count = 0
    while True:
        data, rate_limit = _run_graphql_query(access_token, query, variables)
        top_connection = _extract_top_connection(data, node_type)
        data_items = (
            top_connection["nodes"]
            if "nodes" in top_connection
            else top_connection["edges"]
        )
        items_count += len(data_items)
        print(
            f'Got {len(data_items)}/{items_count} {node_type}s, query cost {rate_limit["cost"]}, remaining credits: {rate_limit["remaining"]}'
        )
        if data_items:
            yield data_items
        else:
            return
        variables["page_after"] = _extract_top_connection(data, node_type)["pageInfo"][
            "endCursor"
        ]
        if max_items and items_count >= max_items:
            print(f"Max items limit reached: {items_count} >= {max_items}")
            return


def _get_comment_reaction(comment_ids: List[str], access_token: str) -> StrAny:
    """Builds a query from a list of comment nodes and returns associated reactions."""
    idx = 0
    data: DictStrAny = {}
    for page_chunk in chunks(comment_ids, 50):
        subs = []
        for comment_id in page_chunk:
            subs.append(COMMENT_REACTIONS_QUERY % (idx, comment_id))
            idx += 1
        subs.append(RATE_LIMIT)
        query = "{" + ",\n".join(subs) + "}"
        page, rate_limit = _run_graphql_query(access_token, query, {})
        print(
            f'Got {len(page)} comments, query cost {rate_limit["cost"]}, remaining credits: {rate_limit["remaining"]}'
        )
        data.update(page)
    return data
