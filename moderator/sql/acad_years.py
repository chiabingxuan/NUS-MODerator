INSERT_NEW_ACAD_YEAR_STATEMENT = """
INSERT INTO acad_years
VALUES (:acad_year);
"""

GET_LIST_OF_AYS_QUERY = """
SELECT a.acad_year
FROM acad_years a
ORDER BY a.acad_year ASC;
"""