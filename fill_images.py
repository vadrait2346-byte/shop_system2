import sqlite3
import os

DB_NAME = "database/shoes_shop.db"
# Укажи точное название твоей папки с картинками, если оно отличается
IMAGES_DIR = "fimoz"

def auto_fill_shoe_images():
    if not os.path.exists(IMAGES_DIR):
        print(f"[ОШИБКА] Папка {IMAGES_DIR} не найдена! Переименуй IMAGES_DIR в коде.")
        return

    # Получаем список всех картинок из папки
    all_images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not all_images:
        print("[ВНИМАНИЕ] Папка с картинками пуста!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Берем всю обувь, которая сейчас есть на складе
    cursor.execute("SELECT id, model_name FROM shoes")
    shoes = cursor.fetchall()

    if not shoes:
        print("[ВНИМАНИЕ] Таблица shoes в базе данных пуста. Сначала добавь модели!")
        conn.close()
        return

    print(f"Найдено моделей в БД: {len(shoes)}. Найдено картинок в папке: {len(all_images)}.")

    # Раскидываем картинки по моделям по очереди
    for i, (shoe_id, model_name) in enumerate(shoes):
        # Чтобы картинки не кончались, берем их по кругу через остаток от деления %
        img_name = all_images[i % len(all_images)]
        full_path = os.path.join(IMAGES_DIR, img_name).replace("\\", "/") # Нормализуем пути для Windows/Linux

        # Записываем путь к картинке в базу данных для конкретного ID обуви
        cursor.execute("UPDATE shoes SET image_path = ? WHERE id = ?", (full_path, shoe_id))

    conn.commit()
    conn.close()
    print("[УСПЕХ] Все пути к картинкам успешно прописаны в базу данных!")

if __name__ == "__main__":
    auto_fill_shoe_images()
