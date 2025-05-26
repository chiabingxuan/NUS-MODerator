GET_BUS_NUMBERS_QUERY = """
SELECT bn.bus_num
FROM bus_numbers bn;
"""

INSERT_BUS_NUMBER_STATEMENT = """
INSERT INTO bus_numbers
VALUES (:bus_num)
ON CONFLICT (bus_num) DO NOTHING;
"""

DELETE_BUS_NUMBER_STATEMENT = """
DELETE FROM bus_numbers bn
WHERE bn.bus_num = :bus_num;
"""