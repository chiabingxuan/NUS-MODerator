GET_BUS_ROUTES_QUERY = """
SELECT *
FROM bus_routes br;
"""

# ANY: Accounts for terminal stops with 2 values of seq_num
GET_SUBSEQUENT_BUS_STOPS_QUERY = """
SELECT br1.bus_stop_code, bs.display_name
FROM bus_routes br1, bus_stops bs
WHERE br1.bus_stop_code = bs.code_name
AND br1.bus_num = :bus_num
AND br1.seq_num > ANY (
    SELECT br2.seq_num
    FROM bus_routes br2
    WHERE br2.bus_num = :bus_num
    AND br2.bus_stop_code = :bus_stop_code
)
ORDER BY br1.seq_num ASC;
"""

GET_TERMINAL_BUS_STOP_QUERY = """
SELECT br.bus_stop_code
FROM bus_routes br
WHERE br.bus_num = :bus_num
AND br.seq_num = :max_seq_num;
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