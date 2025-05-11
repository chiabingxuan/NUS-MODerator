GET_MODULE_CODES_QUERY = """
SELECT m.code
FROM modules m;
"""

INSERT_NEW_MODULE_STATEMENT = """
INSERT INTO modules
VALUES (:code, :title, :department, :description, :num_mcs)
ON CONFLICT (code) DO UPDATE SET
title = EXCLUDED.title, department = EXCLUDED.department, description = EXCLUDED.description, num_mcs = EXCLUDED.num_mcs;
"""

COUNT_EXISTING_MODULES_QUERY = """
SELECT COUNT(m.code) AS num_modules
FROM modules m;
"""

