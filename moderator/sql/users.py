GET_EXISTING_USER_QUERY = """
SELECT *
FROM users u
WHERE u.username = :username;
"""

INSERT_NEW_USER_STATEMENT = """
INSERT INTO users
VALUES (:username, :password, :first_name, :last_name, :matriculation_ay, :major, 'user')
"""