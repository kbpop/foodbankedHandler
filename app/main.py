from flask import Flask, jsonify, request, g
from flask_cors import CORS
from mysql.connector.errors import IntegrityError

from db_utils import (
    connect_to_db,
    get_user_by_email,
    get_or_create_organization,
    create_user,
    list_pending_users,
    set_verification_status,
)
from auth import (
    DONOR,
    EMPLOYEE,
    PARTNER,
    ADMIN,
    hash_password,
    verify_password,
    create_token,
    set_auth_cookie,
    clear_auth_cookie,
    login_required,
    role_required,
)

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

SELF_REGISTERABLE_TYPES = (DONOR, EMPLOYEE, PARTNER)
ORG_TYPE_BY_ACCOUNT_TYPE = {EMPLOYEE: "foodbank", PARTNER: "partner_agency"}


@app.route("/")
def home():
    return "<h1>Hello, World!</h1><p>My new Flask app is running.</p>"


@app.before_request
def get_db():
    if 'mysql_db' not in g:
        g.mysql_db = connect_to_db()
    if g.mysql_db is None and request.path != "/":
        return jsonify({"error": "database connection unavailable"}), 503


@app.teardown_request
def teardown_db(exception):
    db = g.pop('mysql_db', None)
    if db is not None:
        db.close()


@app.route("/user/<int:user_id>")
def profile(user_id):
    cursor = g.mysql_db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, email, account_type, created_at FROM users WHERE id = %s",
        (user_id,),
    )
    user = cursor.fetchone()
    cursor.close()
    return jsonify(user)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    account_type = data.get("accountType")
    organization_name = data.get("organization")

    if not email or not password or account_type not in SELF_REGISTERABLE_TYPES:
        return jsonify({"error": "email, password, and a valid accountType are required"}), 400

    if account_type in ORG_TYPE_BY_ACCOUNT_TYPE and not organization_name:
        return jsonify({"error": "organization is required for this account type"}), 400

    if get_user_by_email(g.mysql_db, email):
        return jsonify({"error": "an account with this email already exists"}), 409

    organization_id = None
    if account_type in ORG_TYPE_BY_ACCOUNT_TYPE:
        organization_id = get_or_create_organization(
            g.mysql_db, organization_name, ORG_TYPE_BY_ACCOUNT_TYPE[account_type]
        )

    verification_status = "verified" if account_type == DONOR else "pending"
    try:
        user_id = create_user(
            g.mysql_db,
            email,
            hash_password(password),
            account_type,
            verification_status,
            organization_id,
        )
    except IntegrityError:
        return jsonify({"error": "an account with this email already exists"}), 409

    return jsonify({
        "id": user_id,
        "email": email,
        "accountType": account_type,
        "verificationStatus": verification_status,
    }), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = get_user_by_email(g.mysql_db, email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "invalid email or password"}), 401

    if user["verification_status"] != "verified":
        return jsonify({"error": "this account is pending administrator verification"}), 403

    response = jsonify({
        "id": user["id"],
        "email": user["email"],
        "accountType": user["account_type"],
    })
    set_auth_cookie(response, create_token(user))
    return response


@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"ok": True})
    clear_auth_cookie(response)
    return response


@app.route("/me")
@login_required
def me():
    return jsonify(g.current_user)


@app.route("/admin/pending")
@role_required(ADMIN)
def admin_pending():
    return jsonify(list_pending_users(g.mysql_db))


@app.route("/admin/verify/<int:user_id>", methods=["POST"])
@role_required(ADMIN)
def admin_verify(user_id):
    data = request.get_json(silent=True) or {}
    approve = data.get("approve", True)
    set_verification_status(g.mysql_db, user_id, "verified" if approve else "rejected")
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
