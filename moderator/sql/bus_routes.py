GET_BUS_ROUTES_QUERY = """
SELECT *
FROM bus_routes br;
"""

INSERT_BUS_ROUTE_STATEMENT = """
INSERT INTO bus_routes
VALUES (:bus_num, :bus_stop_code, :seq_num)
ON CONFLICT (bus_num, bus_stop_code, seq_num) DO NOTHING;
"""

DELETE_BUS_ROUTE_STATEMENT = """
DELETE FROM bus_routes br
WHERE br.bus_num = :bus_num
AND br.bus_stop_code = :bus_stop_code
AND br.seq_num = :seq_num;
"""