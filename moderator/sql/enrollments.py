DELETE_USER_ENROLLMENT_STATEMENT = """
DELETE FROM enrollments e
WHERE e.username = (:username);
"""

INSERT_NEW_ENROLLMENT_STATEMENT = """
INSERT INTO enrollments (username, module_code, acad_year, sem_num)
VALUES (:username, :module_code, :acad_year, :sem_num);
"""

GET_ENROLLMENTS_OF_USER_QUERY = """
SELECT e.acad_year, s.name, e.module_code, m.title
FROM enrollments e, semesters s, modules m
WHERE e.sem_num = s.num
AND e.module_code = m.code
AND e.username = :username
ORDER BY e.acad_year ASC, e.sem_num ASC, e.module_code ASC;
"""