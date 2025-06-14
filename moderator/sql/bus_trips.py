INSERT_BUS_TRIP_STATEMENT = """
INSERT INTO bus_trips
VALUES (:username, :bus_num, :start_bus_stop, :end_bus_stop, :start_date, :end_date, :eta, :weather)
RETURNING start_date;
"""