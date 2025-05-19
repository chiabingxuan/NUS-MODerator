GET_MODULE_CODES_QUERY = """
SELECT m.code
FROM modules m;
"""

INSERT_NEW_MODULE_STATEMENT = """
INSERT INTO modules
VALUES (:code, :title, :department, :description, :num_mcs, :is_year_long)
ON CONFLICT (code) DO UPDATE SET
title = EXCLUDED.title, department = EXCLUDED.department, description = EXCLUDED.description, num_mcs = EXCLUDED.num_mcs, is_year_long = EXCLUDED.is_year_long;
"""

COUNT_SPECIFIC_AY_MODULES_QUERY = """
SELECT COUNT(m.code) AS num_modules
FROM modules m
WHERE EXISTS (
    SELECT *
    FROM offers o
    WHERE o.module_code = m.code
    AND o.acad_year = :acad_year
);
"""

GET_SPECIFIC_TERM_MODULES_QUERY = """
SELECT m.code, m.title
FROM modules m
WHERE EXISTS (
    SELECT *
    FROM offers o
    WHERE o.module_code = m.code
    AND o.acad_year = :acad_year
    AND o.sem_num = :sem_num
)
ORDER BY m.code ASC;
"""

GET_MODULE_INFO_QUERY = """
SELECT *
FROM modules m
WHERE m.code = :code;
"""

GET_MODULES_INFO_FOR_PLANNER_QUERY = """
SELECT m.code, m.num_mcs, m.is_year_long
FROM modules m;
"""

GET_TERMS_OFFERED_FOR_SPECIFIC_MODULE_QUERY = """
SELECT o.sem_num
FROM offers o
WHERE o.module_code = :module_code
AND o.acad_year = :acad_year;
"""