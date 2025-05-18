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

MAKE_USER_ADMIN_STATEMENT = """
UPDATE users
SET u.role = 'admin'
WHERE u.username = :username;
"""