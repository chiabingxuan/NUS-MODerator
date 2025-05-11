INSERT_NEW_DEPARTMENT_STATEMENT = """
INSERT INTO departments
VALUES (:department, :faculty)
ON CONFLICT (department) DO UPDATE SET
faculty = EXCLUDED.faculty;
"""

DELETE_OUTDATED_DEPARTMENTS_STATEMENT = """
DELETE FROM departments d
WHERE NOT EXISTS (
    SELECT *
    FROM modules m
    WHERE m.department = d.department
);
"""

COUNT_EXISTING_DEPARTMENTS_QUERY = """
SELECT COUNT(d.department) AS num_depts
FROM departments d;
"""
