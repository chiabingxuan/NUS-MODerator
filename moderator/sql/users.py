GET_EXISTING_USER_QUERY = """
SELECT *
FROM users u
WHERE u.username = :username;
"""

INSERT_NEW_USER_STATEMENT = """
INSERT INTO users
VALUES (:username, :password, :first_name, :last_name, :matriculation_ay, :major, 'user', :reg_datetime)
"""

COUNT_CURRENT_USERS_QUERY = """
SELECT COUNT(u.username) AS num_users
FROM users u;
"""

COUNT_CURRENT_USERS_BY_DATE_QUERY = """
SELECT DATE(u.reg_datetime) AS date, COUNT(u.username) AS num_users_registered
FROM users u
GROUP BY date
ORDER BY date ASC;
"""

MAKE_USER_ADMIN_STATEMENT = """
UPDATE users
SET role = 'admin'
WHERE username = :username;
"""