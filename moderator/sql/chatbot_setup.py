SET_CONCAT_MAX_LENGTH_STATEMENT = """
SET SESSION group_concat_max_len = 1000000;
"""

GET_MODULE_COMBINED_REVIEWS_QUERY = """
SELECT m.code, m.title, m.description, comb_rev.doc_content
FROM modules m, (
    SELECT r.module_code, GROUP_CONCAT(r.message SEPARATOR '\n\n') AS doc_content
    FROM reviews r
    GROUP BY r.module_code
) AS comb_rev
WHERE m.code = comb_rev.module_code
"""