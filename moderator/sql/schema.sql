CREATE TABLE IF NOT EXISTS departments (
    department VARCHAR(255) PRIMARY KEY,
    faculty VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS majors (
    major VARCHAR(255) PRIMARY KEY,
    department VARCHAR(255) NOT NULL,
    num_years INT NOT NULL,
    FOREIGN KEY (department) REFERENCES departments(department) ON DELETE CASCADE ON UPDATE CASCADE
)

CREATE TABLE IF NOT EXISTS modules (
    code VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT,
    num_mcs NUMERIC(10, 2) NOT NULL,
    is_year_long BOOLEAN NOT NULL,
    FOREIGN KEY (department) REFERENCES departments(department) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (num_mcs >= 0)
);

CREATE TABLE IF NOT EXISTS credit_internships (
    internship_code VARCHAR(255) PRIMARY KEY, 
    FOREIGN KEY (internship_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS iblocs (
    ibloc_code VARCHAR(255) PRIMARY KEY, 
    FOREIGN KEY (ibloc_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS acad_years (
    acad_year VARCHAR(255) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS semesters (
    num INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    min_mcs NUMERIC(10, 2) NOT NULL,
    CHECK (num IN (1, 2, 3, 4)),
    CHECK (min_mcs >= 0)
);

CREATE TABLE IF NOT EXISTS offers (
    module_code VARCHAR(255),
    acad_year VARCHAR(255),
    sem_num INT,
    PRIMARY KEY (module_code, acad_year, sem_num),
    FOREIGN KEY (module_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (acad_year) REFERENCES acad_years(acad_year) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (sem_num) REFERENCES semesters(num) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id VARCHAR(255) PRIMARY KEY,
    module_code VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (module_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    matriculation_ay VARCHAR(255) NOT NULL,
    major VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    reg_datetime TIMESTAMP NOT NULL,
    FOREIGN KEY (matriculation_ay) REFERENCES acad_years(acad_year) ON UPDATE CASCADE,
    FOREIGN KEY (major) REFERENCES majors(major) ON UPDATE CASCADE,
    CHECK (role IN ('user', 'admin'))
);

CREATE TABLE IF NOT EXISTS enrollments (
    username VARCHAR(255),
    module_code VARCHAR(255),
    acad_year VARCHAR(255),
    sem_num INT,
    rating INT,
    PRIMARY KEY (username, module_code, acad_year, sem_num),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (module_code, acad_year, sem_num) REFERENCES offers(module_code, acad_year, sem_num) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS bus_stops (
    code_name VARCHAR(255) PRIMARY KEY,
    display_name VARCHAR(255) UNIQUE NOT NULL,
    latitude NUMERIC(20, 10) NOT NULL,
    longitude NUMERIC(20, 10) NOT NULL
);

CREATE TABLE IF NOT EXISTS bus_numbers (
    bus_num VARCHAR(15) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bus_routes (
    bus_num VARCHAR(15),
    bus_stop_code VARCHAR(255),
    seq_num INT,
    PRIMARY KEY (bus_num, bus_stop_code, seq_num),
    FOREIGN KEY (bus_num) REFERENCES bus_numbers(bus_num) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (bus_stop_code) REFERENCES bus_stops(code_name) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (bus_num, seq_num)
);

CREATE TABLE IF NOT EXISTS bus_trips (
    username VARCHAR(255),
    bus_num VARCHAR(15),
    start_bus_stop VARCHAR(255),
    end_bus_stop VARCHAR(255),
    start_date TIMESTAMP,               -- TODO: Add trigger to make sure trip durations do not overlap for a given user?
    end_date TIMESTAMP NOT NULL,
    eta TIMESTAMP,
    weather VARCHAR(255) NOT NULL,
    PRIMARY KEY (username, bus_num, start_bus_stop, end_bus_stop, start_date),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (bus_num) REFERENCES bus_numbers(bus_num) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (start_bus_stop) REFERENCES bus_stops(code_name) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (end_bus_stop) REFERENCES bus_stops(code_name) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (start_date < end_date)
);

CREATE TABLE IF NOT EXISTS announcements (
    username VARCHAR(255),
    message TEXT,
    publish_date TIMESTAMP,
    PRIMARY KEY (username, message, publish_date),
    FOREIGN KEY (username) REFERENCES users(username) ON UPDATE CASCADE
)