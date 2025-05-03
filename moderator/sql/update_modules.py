# Schema:
# code, title, department, description

COUNT_EXISTING_ROWS_FOR_MODULE_QUERY = """
SELECT COUNT(m.code)
FROM modules m
WHERE m.code = %s;
"""

INSERT_NEW_MODULE_STATEMENT = """
INSERT INTO modules
VALUES (%s, %s, %s, %s);
"""

UPDATE_EXISTING_MODULE_STATEMENT = """
UPDATE modules m
SET m.title = %s, department = %s, description = %s
WHERE m.code = %s;
"""

DELETE_EXISTING_MODULE_STATEMENT = """
DELETE FROM modules m
WHERE m.code = %s;
"""

