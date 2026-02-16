import pymysql
import bcrypt

def encrypt_existing_passwords():
    con = pymysql.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASS"),
    database=os.environ.get("DB_NAME"),
    port=int(os.environ.get("DB_PORT")),
    cursorclass=pymysql.cursors.DictCursor
    )

    cur = con.cursor()

    # Fetch username and password (NO id column in your table)
    cur.execute("SELECT username, password FROM users")
    users = cur.fetchall()

    for user in users:
        password = user["password"]

        # If password is NOT already bcrypt-hashed
        if not password.startswith("$2b$"):
            hashed = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cur.execute(
                "UPDATE users SET password=%s WHERE username=%s",
                (hashed, user["username"])
            )

            print(f"Encrypted password for user: {user['username']}")

    con.commit()
    con.close()
    print("✅ All old passwords encrypted successfully!")

if __name__ == "__main__":
    encrypt_existing_passwords()
