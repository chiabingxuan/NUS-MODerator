# Schema:
# department, faculty

COUNT_EXISTING_ROWS_FOR_DEPARTMENT_QUERY = """
SELECT COUNT(d.department)
FROM departments d
WHERE d.department = %s;
"""

INSERT_NEW_DEPARTMENT_STATEMENT = """
INSERT INTO departments
VALUES (%s, %s);
"""

UPDATE_EXISTING_DEPARTMENT_STATEMENT = """
UPDATE departments d
SET d.faculty = %s
WHERE d.department = %s;
"""

DELETE_OUTDATED_DEPARTMENTS_STATEMENT = """
DELETE FROM departments d
WHERE NOT EXISTS (
    SELECT *
    FROM modules m
    WHERE m.department = d.department
);
"""