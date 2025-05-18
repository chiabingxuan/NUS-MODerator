DELETE_USER_ENROLLMENT_STATEMENT = """
DELETE FROM enrollments e
WHERE e.username = (:username);
"""

INSERT_NEW_ENROLLMENT_STATEMENT = """
INSERT INTO enrollments (username, module_code, acad_year, sem_num)
VALUES (:username, :module_code, :acad_year, :sem_num);
"""