"""
Создание аккаунта для входа в /manage и /admin.

Запуск (из корня проекта):
    python scripts\\create_admin.py

Спросит логин и пароль в консоли (ввод пароля скрыт) и создаст (или
обновит пароль существующего) аккаунт в базе данных. Можно запускать
несколько раз, чтобы создать несколько аккаунтов или сбросить пароль.
"""
import sys
import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app.models import AdminUser
from app.auth import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        username = input("Логин: ").strip()
        if not username:
            print("❌ Логин не может быть пустым")
            return

        password = getpass.getpass("Пароль: ")
        password2 = getpass.getpass("Повтори пароль: ")

        if not password:
            print("❌ Пароль не может быть пустым")
            return

        if password != password2:
            print("❌ Пароли не совпадают")
            return

        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            existing.password_hash = hash_password(password)
            existing.is_active = True
            db.commit()
            print(f"✅ Пароль для '{username}' обновлён")
        else:
            user = AdminUser(username=username, password_hash=hash_password(password), is_active=True)
            db.add(user)
            db.commit()
            print(f"✅ Аккаунт '{username}' создан")

    finally:
        db.close()


if __name__ == "__main__":
    main()
