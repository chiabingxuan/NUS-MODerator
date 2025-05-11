CREATE TABLE IF NOT EXISTS departments (
    department VARCHAR(255) PRIMARY KEY,
    faculty VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    code VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT,
    num_mcs NUMERIC(10, 2) NOT NULL,
    FOREIGN KEY (department) REFERENCES departments(department) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (num_mcs >= 0)
);

CREATE TABLE IF NOT EXISTS semesters (
    num INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    CHECK (num IN (1, 2, 3, 4))
);

CREATE TABLE IF NOT EXISTS offers (
    module_code VARCHAR(255),
    sem_num INT,
    PRIMARY KEY (module_code, sem_num),
    FOREIGN KEY (module_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE,
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
    CHECK (role IN ('user', 'admin'))
);