INSERT_NEW_REVIEW_STATEMENT = """
INSERT INTO reviews
VALUES (:id, :module_code, :message)
ON CONFLICT (id) DO UPDATE SET
module_code = EXCLUDED.module_code, message = EXCLUDED.message;
"""

COUNT_SPECIFIC_AY_REVIEWS_QUERY = """
SELECT COUNT(r.id) AS num_reviews
FROM reviews r
WHERE EXISTS (
    SELECT *
    FROM modules m, offers o
    WHERE r.module_code = m.code
    AND m.code = o.module_code
    AND o.acad_year = :acad_year
);
"""