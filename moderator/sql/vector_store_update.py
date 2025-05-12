GET_MODULE_COMBINED_REVIEWS_QUERY = """
SELECT m.code, m.title, m.description, comb_rev.doc_content
FROM modules m
LEFT JOIN (
    SELECT r.module_code, STRING_AGG(r.message, '\n\n') AS doc_content
    FROM reviews r
    GROUP BY r.module_code
) AS comb_rev
ON m.code = comb_rev.module_code
WHERE EXISTS (
    SELECT *
    FROM offers o
    WHERE o.module_code = m.code
    AND o.acad_year = :acad_year
);
"""