INSERT_NEW_REVIEW_STATEMENT = """
INSERT INTO reviews
VALUES (:id, :module_code, :message)
ON CONFLICT (id) DO UPDATE SET
module_code = EXCLUDED.module_code, message = EXCLUDED.message;
"""

COUNT_EXISTING_REVIEWS_QUERY = """
SELECT COUNT(r.id) AS num_reviews
FROM reviews r;
"""