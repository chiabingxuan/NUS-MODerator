INSERT_NEW_REVIEW_STATEMENT = """
INSERT INTO reviews
VALUES (:id, :module_code, :message)
ON CONFLICT (id) DO UPDATE SET
module_code = EXCLUDED.module_code, message = EXCLUDED.message;
"""