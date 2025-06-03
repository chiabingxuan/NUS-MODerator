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

GET_SPECIFIC_AY_DEPARTMENTS_QUERY = """
SELECT d.department
FROM departments d
WHERE EXISTS (
    SELECT *
    FROM modules m, offers o
    WHERE d.department = m.department
    AND m.code = o.module_code
    AND o.acad_year = :acad_year
)
ORDER BY d.department ASC;
"""
