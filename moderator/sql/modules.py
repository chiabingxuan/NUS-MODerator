# Schema:
# code, title, department, description

GET_MODULE_CODES_QUERY = """
SELECT m.code AS code
FROM modules m;
"""

INSERT_NEW_MODULE_STATEMENT = """
INSERT INTO modules
VALUES (:code, :title, :department, :description)
ON DUPLICATE KEY UPDATE
title = :title, department = :department, description = :description;
"""

DELETE_EXISTING_MODULE_STATEMENT = """
DELETE FROM modules m
WHERE m.code = :code;
"""

