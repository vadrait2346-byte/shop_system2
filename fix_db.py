import sqlite3
import os

DB_NAME = "database/shoes_shop.db"


def hard_fix():
    # Проверяем, существует ли папка и файл
    if not os.path.exists("database"):
        print("Папка database не найдена!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        print("1. Проверяем таблицу shoes...")
        # На всякий случай добавляем новые поля в shoes, если их нет
        try:
            cursor.execute("ALTER TABLE shoes ADD COLUMN category TEXT DEFAULT 'Обувь'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE shoes ADD COLUMN composition TEXT DEFAULT 'Натуральная кожа'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE shoes ADD COLUMN image_path TEXT")
        except sqlite3.OperationalError:
            pass

        print("2. Пересоздаем таблицу orders с правильной структурой...")
        # Переименовываем старую таблицу, чтобы спасти данные если нужно
        try:
            cursor.execute("ALTER TABLE orders RENAME TO temp_orders")
        except sqlite3.OperationalError:
            # Если temp_orders уже есть от прошлых тестов
            cursor.execute("DROP TABLE IF EXISTS temp_orders")
            cursor.execute("ALTER TABLE orders RENAME TO temp_orders")

        # Создаем новую чистую таблицу orders СРАЗУ с нужным полем order_date и pickup_point_id
        cursor.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                shoe_id INTEGER,
                quantity INTEGER,
                status_id INTEGER,
                pickup_point_id INTEGER,
                order_date TEXT DEFAULT (date('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (shoe_id) REFERENCES shoes(id),
                FOREIGN KEY (status_id) REFERENCES statuses(id),
                FOREIGN KEY (pickup_point_id) REFERENCES pickup_points(id)
            )
        """)

        # Пробуем вернуть старые заказы обратно в новую структуру
        try:
            cursor.execute("""
                INSERT INTO orders (id, customer_id, shoe_id, quantity, status_id, pickup_point_id)
                SELECT id, customer_id, shoe_id, quantity, status_id, pickup_point_id FROM temp_orders
            """)
            print("Данные старых заказов успешно перенесены!")
        except Exception as e:
            print(f"Старых заказов не было или не удалось перенести: {e}")

        # Удаляем временную таблицу
        cursor.execute("DROP TABLE IF EXISTS temp_orders")

        conn.commit()
        print("\n[УСПЕХ] База данных полностью готова к работе с карточками по ТЗ!")

    except Exception as main_err:
        print(f"\n[ОШИБКА БЛОКИРОВКИ] База данных все еще занята процессом: {main_err}")
        print("Пожалуйста, перезагрузи PyCharm или компьютер, чтобы снять блокировку файла базы.")
    finally:
        conn.close()


if __name__ == "__main__":
    hard_fix()
