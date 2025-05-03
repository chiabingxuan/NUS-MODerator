# Schema:
# id, module_code, message

COUNT_EXISTING_ROWS_FOR_REVIEW_QUERY = """
SELECT COUNT(r.id)
FROM reviews r
WHERE r.id = %s;
"""

INSERT_NEW_REVIEW_STATEMENT = """
INSERT INTO reviews
VALUES (%s, %s, %s);
"""

UPDATE_EXISTING_REVIEW_STATEMENT = """
UPDATE reviews r
SET r.module_code = %s, r.message = %s
WHERE r.id = %s;
"""