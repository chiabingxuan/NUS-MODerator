GET_BUS_STOP_CODES_QUERY = """
SELECT bs.code_name
FROM bus_stops bs;
"""

INSERT_BUS_STOP_STATEMENT = """
INSERT INTO bus_stops
VALUES (:code_name, :display_name, :latitude, :longitude)
ON CONFLICT (code_name) DO UPDATE SET
display_name = EXCLUDED.display_name, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude;
"""

DELETE_BUS_STOP_STATEMENT = """
DELETE FROM bus_stops bs
WHERE bs.code_name = :code_name;
"""