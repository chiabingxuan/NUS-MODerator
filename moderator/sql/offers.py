INSERT_NEW_OFFER_STATEMENT = """
INSERT INTO offers
VALUES (:module_code, :acad_year, :sem_num)
ON CONFLICT (module_code, acad_year, sem_num) DO NOTHING;
"""
