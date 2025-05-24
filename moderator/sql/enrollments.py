DELETE_USER_ENROLLMENT_STATEMENT = """
DELETE FROM enrollments e
WHERE e.username = :username
AND e.module_code = :module_code
AND e.acad_year = :acad_year
AND e.sem_num = :sem_num;
"""

INSERT_NEW_ENROLLMENT_STATEMENT = """
INSERT INTO enrollments (username, module_code, acad_year, sem_num)
VALUES (:username, :module_code, :acad_year, :sem_num)
ON CONFLICT (username, module_code, acad_year, sem_num) DO NOTHING;
"""

UPDATE_ENROLLMENT_RATING_STATEMENT = """
UPDATE enrollments
SET rating = :rating
WHERE username = :username
AND module_code = :module_code
AND acad_year = :acad_year
AND sem_num = :sem_num;
"""

GET_ENROLLMENTS_OF_USER_QUERY = """
SELECT e.acad_year, s.name, e.module_code, m.title, e.rating
FROM enrollments e, semesters s, modules m
WHERE e.sem_num = s.num
AND e.module_code = m.code
AND e.username = :username
ORDER BY e.acad_year ASC, e.sem_num ASC, e.module_code ASC;
"""