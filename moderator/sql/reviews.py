# Schema:
# id, module_code, message

INSERT_NEW_REVIEW_STATEMENT = """
INSERT INTO reviews
VALUES (:id, :module_code, :message)
ON DUPLICATE KEY UPDATE
module_code = :module_code, message = :message;
"""