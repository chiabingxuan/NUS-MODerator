ADD_NEW_ANNOUNCEMENT_STATEMENT = """
INSERT INTO announcements
VALUES (:username, :message, :publish_date);
"""

GET_LATEST_ANNOUNCEMENTS_QUERY = """
SELECT *
FROM announcements a
ORDER BY a.publish_date DESC
LIMIT :announcement_limit;
"""