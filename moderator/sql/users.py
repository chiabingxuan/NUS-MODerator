GET_EXISTING_USER_QUERY = """
SELECT *
FROM users u
WHERE u.username = :username;
"""

INSERT_NEW_USER_STATEMENT = """
INSERT INTO users
VALUES (:username, :password, :first_name, :last_name, :matriculation_ay, :major, 'user')
"""

COUNT_EXISTING_USERS_QUERY = """
SELECT COUNT(u.username) AS num_users
FROM users u;
"""