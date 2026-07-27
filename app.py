"""
Route definitions for the Notes API.

Auth endpoints (plain Flask views, matching the provided React client):
    POST /signup  -> create a user, return {token, user}
    POST /login   -> verify credentials, return {token, user}
    GET  /me      -> return the current user, given a valid JWT

Resource endpoints (Flask-RESTful), all JWT-protected and scoped to the
current user so nobody can see or change another user's notes:
    GET    /notes       -> paginated list of the current user's notes
    POST   /notes       -> create a note owned by the current user
    PATCH  /notes/<id>  -> update a note (only if it belongs to the user)
    DELETE /notes/<id>  -> delete a note (only if it belongs to the user)
"""
from flask import request, jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from config import app, db, api
from models import User, Note


# Auth routes
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip() if data.get("username") else ""
    password = data.get("password")
    password_confirmation = data.get("password_confirmation")

    errors = []
    if not username:
        errors.append("Username must be present")
    if not password:
        errors.append("Password must be present")
    if password and password_confirmation is not None and password != password_confirmation:
        errors.append("Password and password confirmation must match")

    if errors:
        return make_response(jsonify({"errors": errors}), 422)

    if User.query.filter_by(username=username).first():
        return make_response(jsonify({"errors": ["Username already taken"]}), 422)

    try:
        user = User(username=username)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return make_response(jsonify({"errors": [str(e)]}), 422)

    token = create_access_token(identity=str(user.id))
    return make_response(jsonify({"token": token, "user": user.to_dict()}), 201)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user and password and user.authenticate(password):
        token = create_access_token(identity=str(user.id))
        return make_response(jsonify({"token": token, "user": user.to_dict()}), 200)

    return make_response(jsonify({"errors": ["Invalid username or password"]}), 401)


@app.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return make_response(jsonify({"errors": ["User not found"]}), 404)
    return make_response(jsonify(user.to_dict()), 200)


# Note resource (Flask-RESTful)
class NoteIndex(Resource):
    """GET /notes (paginated, current user only), POST /notes."""

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
        except ValueError:
            return make_response(jsonify({"errors": ["page and per_page must be integers"]}), 400)

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        pagination = (
            Note.query.filter_by(user_id=user_id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return make_response(
            jsonify(
                {
                    "notes": [note.to_dict() for note in pagination.items],
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                }
            ),
            200,
        )

    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        try:
            note = Note(
                title=data.get("title"),
                content=data.get("content"),
                user_id=user_id,
            )
            db.session.add(note)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return make_response(jsonify({"errors": [str(e)]}), 422)

        return make_response(jsonify(note.to_dict()), 201)


class NoteByID(Resource):
    """PATCH /notes/<id>, DELETE /notes/<id> — owner only."""

    def _get_owned_note_or_error(self, id):
        """Look up a note and confirm it belongs to the current user.

        Returns (note, None) on success, or (None, response) on failure.
        A note that exists but belongs to someone else is treated the same
        as a missing note (404) so we don't leak which IDs exist.
        """
        user_id = int(get_jwt_identity())
        note = Note.query.get(id)
        if not note or note.user_id != user_id:
            return None, make_response(jsonify({"errors": ["Note not found"]}), 404)
        return note, None

    @jwt_required()
    def patch(self, id):
        note, error = self._get_owned_note_or_error(id)
        if error:
            return error

        data = request.get_json() or {}
        try:
            if "title" in data:
                note.title = data["title"]
            if "content" in data:
                note.content = data["content"]
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return make_response(jsonify({"errors": [str(e)]}), 422)

        return make_response(jsonify(note.to_dict()), 200)

    @jwt_required()
    def delete(self, id):
        note, error = self._get_owned_note_or_error(id)
        if error:
            return error

        db.session.delete(note)
        db.session.commit()
        return make_response("", 204)


api.add_resource(NoteIndex, "/notes")
api.add_resource(NoteByID, "/notes/<int:id>")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
