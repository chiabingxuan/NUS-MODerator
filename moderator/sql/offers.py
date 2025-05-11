INSERT_NEW_OFFER_STATEMENT = """
INSERT INTO offers
VALUES (:module_code, :sem_num)
ON CONFLICT (module_code, sem_num) DO NOTHING;
"""

DELETE_EXISTING_OFFER_STATEMENT = """
DELETE FROM offers o
WHERE o.module_code = :module_code AND o.sem_num = :sem_num;
"""