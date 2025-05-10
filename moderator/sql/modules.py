GET_MODULE_CODES_QUERY = """
SELECT m.code
FROM modules m;
"""

INSERT_NEW_MODULE_STATEMENT = """
INSERT INTO modules
VALUES (:code, :title, :department, :description)
ON CONFLICT (code) DO UPDATE SET
title = EXCLUDED.title, department = EXCLUDED.department, description = EXCLUDED.description;
"""

DELETE_EXISTING_MODULE_STATEMENT = """
DELETE FROM modules m
WHERE m.code = :code;
"""

