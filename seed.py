"""
Seed the database with example users and notes.

Run with:  python seed.py
"""
from faker import Faker

from config import app, db
from models import User, Note

fake = Faker()


def seed():
    with app.app_context():
        print("Clearing existing data...")
        Note.query.delete()
        User.query.delete()
        db.session.commit()

        print("Seeding users...")
        users = []
        # A couple of known logins for easy manual testing.
        for username, password in [("alice", "password123"), ("bob", "password123")]:
            user = User(username=username)
            user.password_hash = password
            users.append(user)
            db.session.add(user)

        # A handful of extra random users.
        for _ in range(3):
            user = User(username=fake.unique.user_name())
            user.password_hash = "password123"
            users.append(user)
            db.session.add(user)

        db.session.commit()

        print("Seeding notes...")
        for user in users:
            for _ in range(5):
                note = Note(
                    title=fake.sentence(nb_words=4).rstrip("."),
                    content=fake.paragraph(nb_sentences=3),
                    user_id=user.id,
                )
                db.session.add(note)

        db.session.commit()
        print(f"Done! Seeded {len(users)} users and {len(users) * 5} notes.")
        print("Test login -> username: alice, password: password123")


if __name__ == "__main__":
    seed()
