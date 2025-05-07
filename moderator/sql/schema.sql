CREATE TABLE IF NOT EXISTS departments (
    department VARCHAR(255) PRIMARY KEY,
    faculty VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    code VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT,
    FOREIGN KEY (department) REFERENCES departments(department) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id VARCHAR(255) PRIMARY KEY,
    module_code VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (module_code) REFERENCES modules(code) ON DELETE CASCADE ON UPDATE CASCADE
);