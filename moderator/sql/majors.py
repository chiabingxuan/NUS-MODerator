GET_MAJORS_QUERY = """
SELECT *
FROM majors m
ORDER BY m.major ASC;
"""

GET_EXISTING_MAJOR_QUERY = """
SELECT *
FROM majors m
WHERE m.major = :major;
"""

INSERT_NEW_MAJOR_QUERY = """
INSERT INTO majors
VALUES (:major, :department);
"""