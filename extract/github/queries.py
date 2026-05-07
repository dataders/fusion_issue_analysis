RATE_LIMIT = """
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
"""

ISSUES_QUERY = """
query($owner: String!, $name: String!, $issues_per_page: Int!, $first_reactions: Int!, $first_comments: Int!, $first_timeline_items: Int!, $page_after: String) {
  repository(owner: $owner, name: $name) {
    %s(first: $issues_per_page, orderBy: {field: CREATED_AT, direction: DESC}, after: $page_after) {
      totalCount
      pageInfo {
        endCursor
        startCursor
      }
      nodes {
        # id
        number
        url
        title
        body
        author {login avatarUrl url}
        authorAssociation
        closed
        closedAt
        createdAt
        state
        updatedAt
        __ISSUE_TYPE_FRAGMENT__
        labels(first: 25) {
          nodes {
            name
            color
            description
          }
        }
        milestone {
          number
          title
          description
          state
          dueOn
          createdAt
          closedAt
        }
        assignees(first: 10) {
          nodes {
            login
            avatarUrl
            url
          }
        }
        reactions(first: $first_reactions) {
          totalCount
          nodes {
            # id
            user {login avatarUrl url}
            content
            createdAt
          }
        }
        timelineItems(first: $first_timeline_items, itemTypes: [LABELED_EVENT, UNLABELED_EVENT]) {
          totalCount
          nodes {
            __typename
            ... on LabeledEvent {
              createdAt
              actor {login avatarUrl url}
              label {name color}
            }
            ... on UnlabeledEvent {
              createdAt
              actor {login avatarUrl url}
              label {name color}
            }
          }
        }
        comments(first: $first_comments) {
          totalCount
          nodes {
            id
            url
            body
            author {avatarUrl login url}
            authorAssociation
            createdAt
            reactionGroups {content createdAt}
            # reactions(first: 0) {
            #   totalCount
            #   nodes {
            #     # id
            #     user {login avatarUrl url}
            #     content
            #     createdAt
            #   }
            # }
          }
        }
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
"""

COMMENT_REACTIONS_QUERY = """
node_%s: node(id:"%s") {
     ... on IssueComment {
      id
      reactions(first: 100) {
        totalCount
        nodes {
            user {login avatarUrl url}
            content
            createdAt
          }
      }
    }
  }
"""

STARGAZERS_QUERY = """
query($owner: String!, $name: String!, $items_per_page: Int!, $page_after: String) {
  repository(owner: $owner, name: $name) {
    stargazers(first: $items_per_page, orderBy: {field: STARRED_AT, direction: DESC}, after: $page_after) {
      pageInfo {
        endCursor
        startCursor
      }
      edges {
        starredAt
        node {
          login
          avatarUrl
          url
        }
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
"""
