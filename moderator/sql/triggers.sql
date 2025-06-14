-- CHECKING THE SAVING OF BUS TRIPS --
-- For a given user, time range of bus trips should not overlap
CREATE FUNCTION handle_trips()
RETURNS TRIGGER AS
$$
DECLARE
    num_overlapping_trips INTEGER;
BEGIN
    -- For the given user, get number of existing trips whose time range overlaps with this new one
    SELECT COUNT(bt.username)
    INTO num_overlapping_trips
    FROM bus_trips bt
    WHERE bt.username = NEW.username
    AND bt.end_date > NEW.start_date
    AND bt.start_date < NEW.end_date;

    IF num_overlapping_trips > 0 THEN
        -- There are overlapping trips, so skip the insertion of this new trip
        RETURN NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_trip_added
BEFORE INSERT ON bus_trips
FOR EACH ROW
EXECUTE FUNCTION handle_trips();


-- INTERCEPTING THE MAKING OF ANNOUNCEMENTS --
-- Only admins can insert into announcements table
CREATE FUNCTION handle_announcements()
RETURNS TRIGGER AS
$$
DECLARE
    role VARCHAR;
BEGIN
    -- Get role of the user making the announcement
    SELECT u.role
    INTO role
    FROM users u
    WHERE u.username = NEW.username;

    IF role != 'admin' THEN
        -- User is not admin, so skip the insertion of announcement
        RETURN NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_announcement_made
BEFORE INSERT ON announcements
FOR EACH ROW
EXECUTE FUNCTION handle_announcements();