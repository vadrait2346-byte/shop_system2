import sys
import sqlite3
import hashlib
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox,
                             QStackedWidget, QTableWidget, QTableWidgetItem, QComboBox, QTabWidget, QInputDialog,
                             QListWidget, QGridLayout)
from PyQt6.QtWidgets import QFrame, QListWidget, QListWidgetItem
from PyQt6.QtGui import QPixmap


class ShoeCardWidget(QFrame):
    """Кастомный виджет карточки товара строго по макету из ТЗ"""

    def __init__(self, brand, model_name, category, composition, price, total_stock, size=None, has_discount=False,
                 img_path=None):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Фиксируем высоту карточки, чтобы она не растягивалась вертикально
        self.setFixedHeight(120)

        # ТЗ: Если доступное количество <= 3, подсвечиваем цветом #FF8080
        if total_stock <= 3:
            self.setStyleSheet("background-color: #FF8080; border: 1px solid #70B2AF; border-radius: 6px;")
        else:
            self.setStyleSheet("background-color: #FFFFFF; border: 1px solid #70B2AF; border-radius: 6px;")

        # Главный горизонтальный контейнер для всей карточки
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 15, 10)
        main_layout.setSpacing(15)

        # 1. ЛЕВАЯ ЧАСТЬ: Изображение товара (контейнер с фиксированным размером)
        self.lbl_image = QLabel()
        self.lbl_image.setFixedSize(130, 100)
        self.lbl_image.setScaledContents(True)

        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
        else:
            pixmap = QPixmap("resources/picture.png")

        if pixmap.isNull():
            pixmap = QPixmap(130, 100)
            pixmap.fill(Qt.GlobalColor.lightGray)

        self.lbl_image.setPixmap(pixmap)
        main_layout.addWidget(self.lbl_image)

        # 2. ЦЕНТРАЛЬНАЯ ЧАСТЬ: Вся инфа о модели (Бренд, Название, Текст)
        center_widget = QWidget()
        center_widget.setStyleSheet("background: transparent;")  # Чтобы не перекрывать фоновый цвет дефицита
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        # ТЗ требует: Производство (Бренд) + Наименование
        lbl_title = QLabel(f"<b>{brand}</b> — {model_name}")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #000000;")

        # Собираем характеристики в красивую строчку
        size_info = f" | Размер: {size}" if size else ""
        lbl_info = QLabel(f"Категория: {category}{size_info}<br>Состав: {composition}")
        lbl_info.setStyleSheet("font-size: 12px; color: #333333;")

        # ТЗ: Вывод «много», если суммарно > 5, и «мало», если 5 или менее
        stock_text = "много" if total_stock > 5 else "мало"
        lbl_stock = QLabel(f"Наличие: <b>{stock_text}</b> ({total_stock} шт.)")
        lbl_stock.setStyleSheet("font-size: 12px; color: #555555;")

        center_layout.addWidget(lbl_title)
        center_layout.addWidget(lbl_info)
        center_layout.addWidget(lbl_stock)
        center_layout.addStretch()

        # Добавляем центр в главный лейаут
        main_layout.addWidget(center_widget)

        # Пружина-распорка: выталкивает цену в самый правый угол карточки
        main_layout.addStretch()

        # 3. ПРАВАЯ ЧАСТЬ: Блок цены (прижат вправо)
        if has_discount:
            final_price = price * 0.75
            price_text = f"<span style='color: #777777; text-decoration: line-through; font-size: 12px;'>{int(price)} руб.</span><br><span style='color: #D11A2A; font-weight: bold; font-size: 16px;'>{int(final_price)} руб.</span>"
        else:
            final_price = price
            price_text = f"<span style='font-weight: bold; font-size: 16px; color: #000000;'>{int(final_price)} руб.</span>"

        lbl_price = QLabel(price_text)
        lbl_price.setStyleSheet("background: transparent;")
        lbl_price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(lbl_price)

        self.setLayout(main_layout)


DB_NAME = "database/shoes_shop.db"


class LoginWindow(QWidget):
    """Окно авторизации с гарантированной очисткой текстовой роли"""

    def __init__(self, switch_window_callback):
        super().__init__()
        self.switch_window = switch_window_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Вход в систему учета обуви")
        self.setFixedSize(350, 250)

        layout = QVBoxLayout()

        self.lbl_title = QLabel("Авторизация", alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.lbl_title)

        self.txt_login = QLineEdit(placeholderText="Логин")
        layout.addWidget(self.txt_login)

        self.txt_password = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_password)

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.handle_login)
        layout.addWidget(btn_login)

        btn_guest = QPushButton("Войти как гость")
        btn_guest.setStyleSheet("background-color: #d3d3d3;")
        btn_guest.clicked.connect(lambda: self.switch_window("guest"))
        layout.addWidget(btn_guest)

        self.setLayout(layout)

    def handle_login(self):
        login = self.txt_login.text().strip()
        password = self.txt_password.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.name FROM users u 
                JOIN roles r ON u.role_id = r.id 
                WHERE u.login = ? AND u.password = ?
            ''', (login, password_hash))
            result = cursor.fetchone()
            conn.close()

            if result:
                # Извлекаем строго нулевой элемент кортежа и очищаем его от пробелов
                clean_role_name = str(result[0]).strip().lower()
                self.switch_window(clean_role_name)
            else:
                QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось выполнить вход: {e}")


class MainWindow(QWidget):
    """Главное окно приложения под 3НФ структуру с пунктами выдачи"""

    def __init__(self, role, logout_callback):
        super().__init__()
        # Принудительно очищаем и приводим роль к нижнему регистру для проверок
        self.role = str(role).strip().lower()
        self.logout = logout_callback

        self.is_initialized = False
        self.init_ui()

        if self.role in ["manager", "admin"]:
            self.update_filter_comboboxes()

        self.is_initialized = True

        self.load_shoes_data()
        if self.role in ["manager", "admin"]:
            self.load_orders_data()

    def init_ui(self):
        self.setWindowTitle(f"Система учета — Роль: {self.role.upper()}")
        self.setMinimumSize(950, 650)

        main_layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        lbl_role = QLabel(f"Вы вошли как: <b>{self.role}</b>")
        btn_logout = QPushButton("Выйти из системы")
        btn_logout.clicked.connect(self.logout)
        top_bar.addWidget(lbl_role)
        top_bar.addStretch()
        top_bar.addWidget(btn_logout)
        main_layout.addLayout(top_bar)

        # !!! ВОТ ЭТА СТРОЧКА ДОЛЖНА СТОЯТЬ ТУТ ОБЯЗАТЕЛЬНО !!!
        self.tabs = QTabWidget()

        # --- ВКЛАДКА 1: ТОВАРЫ ---
        self.tab_shoes = QWidget()
        shoes_layout = QVBoxLayout()
        # ... дальше весь код первой вкладки, что мы писали ранее ...

        # --- ВКЛАДКА 1: ТОВАРЫ (ВОЗВРАЩАЕМ НА МЕСТО) ---
        self.tab_shoes = QWidget()
        shoes_layout = QVBoxLayout()

        # Фильтры для менеджера и админа (поиск, сортировка и т.д.)
        if self.role in ["manager", "admin"]:
            filter_box = QVBoxLayout()
            row1 = QHBoxLayout()
            self.txt_search = QLineEdit(placeholderText="Поиск по названию модели...")
            self.txt_search.textChanged.connect(self.load_shoes_data)

            self.cmb_sort = QComboBox()
            self.cmb_sort.addItems(["Без сортировки", "Цена: по возрастанию", "Остаток: по убыванию"])
            self.cmb_sort.currentIndexChanged.connect(self.load_shoes_data)

            row1.addWidget(QLabel("Поиск:"))
            row1.addWidget(self.txt_search)
            row1.addWidget(QLabel("Сортировка:"))
            row1.addWidget(self.cmb_sort)
            filter_box.addLayout(row1)

            row2 = QHBoxLayout()
            self.cmb_brand = QComboBox()
            self.cmb_brand.currentIndexChanged.connect(self.load_shoes_data)

            self.cmb_size = QComboBox()
            self.cmb_size.currentIndexChanged.connect(self.load_shoes_data)

            self.cmb_price = QComboBox()
            self.cmb_price.addItems(["Все цены", "До 10 000 руб.", "От 10 000 руб."])
            self.cmb_price.currentIndexChanged.connect(self.load_shoes_data)

            self.cmb_stock = QComboBox()
            self.cmb_stock.addItems(["Любой остаток", "Только в наличии (>0)", "Мало на складе (≤5)"])
            self.cmb_stock.currentIndexChanged.connect(self.load_shoes_data)

            row2.addWidget(QLabel("Бренд:"))
            row2.addWidget(self.cmb_brand)
            row2.addWidget(QLabel("Размер:"))
            row2.addWidget(self.cmb_size)
            row2.addWidget(QLabel("Стоимость:"))
            row2.addWidget(self.cmb_price)
            row2.addWidget(QLabel("Наличие:"))
            row2.addWidget(self.cmb_stock)
            filter_box.addLayout(row2)
            shoes_layout.addLayout(filter_box)

        # НАШ НОВЫЙ СПИСОК КАРТОЧЕК ТОВАРОВ
        self.table_shoes = QListWidget()
        self.table_shoes.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.table_shoes.setStyleSheet("border: 1px solid #70B2AF; background-color: #FFFFFF;")
        shoes_layout.addWidget(self.table_shoes)

        # Кнопки управления для админа на вкладке товаров
        if self.role == "admin":
            admin_shoes_bar = QHBoxLayout()
            btn_add_shoe = QPushButton("Добавить обувь")
            btn_edit_shoe = QPushButton("Изменить остаток")
            btn_del_shoe = QPushButton("Удалить модель")

            btn_add_shoe.clicked.connect(self.add_shoe)
            btn_edit_shoe.clicked.connect(self.edit_shoe_stock)
            btn_del_shoe.clicked.connect(self.delete_shoe)

            admin_shoes_bar.addWidget(btn_add_shoe)
            admin_shoes_bar.addWidget(btn_edit_shoe)
            admin_shoes_bar.addWidget(btn_del_shoe)
            shoes_layout.addLayout(admin_shoes_bar)

        self.tab_shoes.setLayout(shoes_layout)

        # САМАЯ ВАЖНАЯ СТРОЧКА: добавляем вкладку товаров в общий контейнер вкладок
        self.tabs.addTab(self.tab_shoes, "Склад / Товары")

        # --- ВКЛАДКА 2: ЗАКАЗЫ (с пунктами выдачи) ---
        if self.role in ["manager", "admin"]:
            self.tab_orders = QWidget()
            orders_layout = QVBoxLayout()

            self.table_orders = QTableWidget()
            self.table_orders.setColumnCount(7)  # Увеличено до 7 колонок
            self.table_orders.setHorizontalHeaderLabels(
                ["ID Заказа", "Клиент", "Бренд", "Модель", "Кол-во", "Статус", "Пункт выдачи"])
            orders_layout.addWidget(self.table_orders)

            if self.role == "admin":
                admin_orders_bar = QHBoxLayout()
                btn_add_order = QPushButton("Создать заказ")
                btn_edit_order = QPushButton("Изменить статус")
                btn_del_order = QPushButton("Аннулировать заказ")

                btn_add_order.clicked.connect(self.add_order)
                btn_edit_order.clicked.connect(self.edit_order_status)
                btn_del_order.clicked.connect(self.delete_order)

                admin_orders_bar.addWidget(btn_add_order)
                admin_orders_bar.addWidget(btn_edit_order)
                admin_orders_bar.addWidget(btn_del_order)
                orders_layout.addLayout(admin_orders_bar)

            self.tab_orders.setLayout(orders_layout)
            self.tabs.addTab(self.tab_orders, "Управление заказами")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def update_filter_comboboxes(self):
        """Безопасное динамическое заполнение списков фильтров"""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM brands ORDER BY name ASC")
            brands = [str(row[0]) for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT size FROM shoes ORDER BY size ASC")
            sizes = [str(row[0]) for row in cursor.fetchall()]
            conn.close()

            if hasattr(self, 'cmb_brand') and hasattr(self, 'cmb_size'):
                self.cmb_brand.blockSignals(True)
                self.cmb_size.blockSignals(True)

                self.cmb_brand.clear()
                self.cmb_brand.addItem("Все бренды")
                self.cmb_brand.addItems(brands)

                self.cmb_size.clear()
                self.cmb_size.addItem("Все размеры")
                self.cmb_size.addItems(sizes)

                self.cmb_brand.blockSignals(False)
                self.cmb_size.blockSignals(False)
        except Exception as e:
            print(f"Ошибка обновления комбобоксов: {e}")

    # --- ЛОГИКА РАБОТЫ С ТОВАРАМИ (3НФ) ---
    def load_shoes_data(self):
        if not self.is_initialized:
            return

        self.table_shoes.blockSignals(True)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # SQL-запрос с проверкой отсутствия заказов в предыдущем календарном месяце.
            # Если заказов не было, то COUNT(o.id) вернет 0, и flag_discount станет равен 1.
            # Также добавлены поля category, composition и image_path для карточек по ТЗ.
            query = """
                SELECT 
                    s.id, 
                    b.name AS brand_name, 
                    s.model_name, 
                    s.size, 
                    s.price, 
                    s.stock,
                    COALESCE(s.category, 'Обувь') AS category,
                    COALESCE(s.composition, 'Натуральный материал') AS composition,
                    s.image_path,
                    CASE 
                        WHEN (
                            SELECT COUNT(o.id) 
                            FROM orders o 
                            WHERE o.shoe_id = s.id 
                              AND strftime('%Y-%m', o.order_date) = strftime('%Y-%m', 'now', '-1 month')
                        ) = 0 THEN 1 
                        ELSE 0 
                    END AS flag_discount
                FROM shoes s
                JOIN brands b ON s.brand_id = b.id
                WHERE 1=1
            """
            params = []

            # Сохраняем функционал фильтров и поиска для менеджера и админа
            if self.role in ["manager", "admin"]:
                if hasattr(self, 'txt_search') and self.txt_search.text().strip():
                    query += " AND s.model_name LIKE ?"
                    params.append(f"%{self.txt_search.text().strip()}%")

                if hasattr(self, 'cmb_brand') and self.cmb_brand.currentIndex() > 0:
                    query += " AND b.name = ?"
                    params.append(self.cmb_brand.currentText())

                if hasattr(self, 'cmb_size') and self.cmb_size.currentIndex() > 0:
                    query += " AND s.size = ?"
                    params.append(float(self.cmb_size.currentText()))

                if hasattr(self, 'cmb_price'):
                    price_idx = self.cmb_price.currentIndex()
                    if price_idx == 1:
                        query += " AND s.price < 10000"
                    elif price_idx == 2:
                        query += " AND s.price >= 10000"

                if hasattr(self, 'cmb_stock'):
                    stock_idx = self.cmb_stock.currentIndex()
                    if stock_idx == 1:
                        query += " AND s.stock > 0"
                    elif stock_idx == 2:
                        query += " AND s.stock <= 5"

                if hasattr(self, 'cmb_sort'):
                    sort_idx = self.cmb_sort.currentIndex()
                    if sort_idx == 1:
                        query += " ORDER BY s.price ASC"
                    elif sort_idx == 2:
                        query += " ORDER BY s.stock DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            # Очищаем QListWidget перед новой загрузкой
            self.table_shoes.clear()

            # Наполняем список кастомными карточками
            for row in rows:
                shoe_id, brand, model_name, size, price, stock, category, composition, img_path, has_discount = row

                item = QListWidgetItem(self.table_shoes)

                # Добавили size=size в аргументы
                card_widget = ShoeCardWidget(
                    brand=brand,
                    model_name=model_name,
                    category=category,
                    composition=composition,
                    price=price,
                    total_stock=stock,
                    size=size,
                    has_discount=bool(has_discount),
                    img_path=img_path
                )

                item.setSizeHint(card_widget.sizeHint())
                item.setData(Qt.ItemDataRole.UserRole, shoe_id)
                self.table_shoes.setItemWidget(item, card_widget)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить товары: {e}")

        self.table_shoes.blockSignals(False)

    def load_orders_data(self):
        if not self.is_initialized or not hasattr(self, 'table_orders'):
            return

        self.table_orders.blockSignals(True)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            # Добавлен JOIN с pickup_points для вывода адреса
            cursor.execute("""
                SELECT o.id, c.full_name, b.name, s.model_name, o.quantity, st.name, p.address 
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN shoes s ON o.shoe_id = s.id
                JOIN brands b ON s.brand_id = b.id
                JOIN statuses st ON o.status_id = st.id
                JOIN pickup_points p ON o.pickup_point_id = p.id
            """)
            rows = cursor.fetchall()
            conn.close()

            self.table_orders.setRowCount(0)
            for r_idx, row in enumerate(rows):
                self.table_orders.insertRow(r_idx)
                for c_idx, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.table_orders.setItem(r_idx, c_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить заказы: {e}")
        self.table_orders.blockSignals(False)

    def add_shoe(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM brands")
            brands_data = cursor.fetchall()
            brand_names = [str(b[1]) for b in brands_data]

            if not brand_names:
                QMessageBox.critical(self, "Ошибка", "В базе данных нет брендов!")
                conn.close()
                return

            brand_name, ok1 = QInputDialog.getItem(self, "Бренд", "Выберите бренд:", brand_names, 0, False)
            if not ok1:
                conn.close()
                return

            brand_id = [b[0] for b in brands_data if b[1] == brand_name][0]

            name, ok2 = QInputDialog.getText(self, "Модель", "Введите название модели:")
            if not ok2 or not name.strip():
                conn.close()
                return

            size, ok3 = QInputDialog.getDouble(self, "Размер", "Введите размер:", 40.0, 15.0, 50.0, 1)
            if not ok3:
                conn.close()
                return

            price, ok4 = QInputDialog.getInt(self, "Цена", "Введите цену (руб.):", 5000, 100, 1000000, 100)
            if not ok4:
                conn.close()
                return

            stock, ok5 = QInputDialog.getInt(self, "Остаток", "Количество на складе:", 10, 0, 10000, 1)
            if not ok5:
                conn.close()
                return

            cursor.execute("INSERT INTO shoes (model_name, brand_id, size, price, stock) VALUES (?, ?, ?, ?, ?)",
                           (name.strip(), brand_id, size, float(price), stock))
            conn.commit()
            conn.close()

            self.update_filter_comboboxes()
            self.load_shoes_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товар: {e}")

    def edit_shoe_stock(self):
        # 1. Получаем выделенный элемент из QListWidget вместо таблицы
        current_item = self.table_shoes.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите карточку товара из списка!")
            return

        # 2. Вытаскиваем скрытый ID товара, который мы привязали к карточке
        shoe_id = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Подтягиваем текущий остаток из базы, чтобы показать его в окошке ввода
            cursor.execute("SELECT model_name, stock FROM shoes WHERE id = ?", (shoe_id,))
            res = cursor.fetchone()
            if not res:
                conn.close()
                return
            model_name, current_stock = res

            # Вызываем диалоговое окно
            new_stock, ok = QInputDialog.getInt(
                self, "Изменить остаток",
                f"Введите новый остаток для модели '{model_name}':",
                value=current_stock, min=0
            )

            if ok:
                cursor.execute("UPDATE shoes SET stock = ? WHERE id = ?", (new_stock, shoe_id))
                conn.commit()
                QMessageBox.information(self, "Успех", "Остаток на складе успешно обновлен!")

            conn.close()
            # Перезагружаем список, чтобы сразу увидеть изменения (и смену цвета подсветки, если нужно)
            self.load_shoes_data()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось изменить остаток: {e}")

    def delete_shoe(self):
        # 1. Получаем выделенный элемент из QListWidget
        current_item = self.table_shoes.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите карточку товара для удаления!")
            return

        # 2. Вытаскиваем ID товара
        shoe_id = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Проверяем имя модели для красивого сообщения
            cursor.execute("SELECT model_name FROM shoes WHERE id = ?", (shoe_id,))
            res = cursor.fetchone()
            model_name = res[0] if res else "Выбранная модель"

            # Спрашиваем подтверждение
            confirm = QMessageBox.question(
                self, "Подтверждение удаления",
                f"Вы уверены, что хотите навсегда удалить модель '{model_name}' из базы данных?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm == QMessageBox.StandardButton.Yes:
                # Пробуем удалить. Если на модель завязан чей-то заказ, сработает IntegrityError (3НФ!)
                cursor.execute("DELETE FROM shoes WHERE id = ?", (shoe_id,))
                conn.commit()
                QMessageBox.information(self, "Успех", "Модель успешно удалена из базы данных!")

            conn.close()
            # Обновляем интерфейс
            self.load_shoes_data()

        except sqlite3.IntegrityError:
            QMessageBox.critical(
                self, "Ошибка удаления",
                "Невозможно удалить эту модель обуви, так как на неё уже оформлены активные заказы клиентов!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить модель: {e}")

    def add_order(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute("SELECT id, full_name FROM customers")
            cust_data = cursor.fetchall()
            cust_names = [str(c[1]) for c in cust_data]

            if not cust_names:
                QMessageBox.critical(self, "Ошибка", "В базе нет зарегистрированных клиентов!")
                conn.close()
                return

            cust_name, ok1 = QInputDialog.getItem(self, "Клиент", "Выберите клиента:", cust_names, 0, False)
            if not ok1:
                conn.close()
                return
            customer_id = [c[0] for c in cust_data if c[1] == cust_name][0]

            shoe_id, ok2 = QInputDialog.getInt(self, "Товар", "Введите ID обуви (из первой вкладки):", 1, 1, 100000, 1)
            if not ok2:
                conn.close()
                return

            cursor.execute("SELECT stock FROM shoes WHERE id = ?", (shoe_id,))
            res = cursor.fetchone()
            if not res:
                QMessageBox.critical(self, "Ошибка", "Товара с таким ID нет!")
                conn.close()
                return

            max_stock = res[0]
            if max_stock <= 0:
                QMessageBox.critical(self, "Ошибка", "Этого товара нет на складе!")
                conn.close()
                return

            quantity, ok3 = QInputDialog.getInt(self, "Количество",
                                                f"Доступно на складе {max_stock} шт.\nУкажите количество:", 1, 1,
                                                max_stock, 1)
            if not ok3:
                conn.close()
                return

            cursor.execute("SELECT id, address FROM pickup_points")
            points_data = cursor.fetchall()
            point_addresses = [str(p[1]) for p in points_data]

            if not point_addresses:
                QMessageBox.critical(self, "Ошибка", "В базе нет пунктов выдачи!")
                conn.close()
                return

            point_address, ok4 = QInputDialog.getItem(self, "Пункт выдачи", "Выберите адрес доставки:", point_addresses,
                                                      0, False)
            if not ok4:
                conn.close()
                return
            pickup_point_id = [p[0] for p in points_data if p[1] == point_address][0]

            cursor.execute("SELECT id FROM statuses WHERE name = 'Новый'")
            status_res = cursor.fetchone()
            status_id = status_res[0] if status_res else 1

            cursor.execute("UPDATE shoes SET stock = stock - ? WHERE id = ?", (quantity, shoe_id))
            cursor.execute("""
                INSERT INTO orders (customer_id, shoe_id, quantity, status_id, pickup_point_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, shoe_id, quantity, status_id, pickup_point_id))
            conn.commit()
            conn.close()

            self.load_shoes_data()
            self.load_orders_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заказ: {e}")

    def edit_order_status(self):
        selected = self.table_orders.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите строку с заказом!")
            return
        try:
            order_id = self.table_orders.item(selected, 0).text()

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM statuses")
            st_data = cursor.fetchall()
            st_names = [str(st[1]) for st in st_data]

            status_name, ok = QInputDialog.getItem(self, "Статус", "Выберите статус:", st_names, 0, False)
            if not ok:
                conn.close()
                return
            status_id = [st[0] for st in st_data if st[1] == status_name][0]

            cursor.execute("UPDATE orders SET status_id = ? WHERE id = ?", (status_id, order_id))
            conn.commit()
            conn.close()
            self.load_orders_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить статус: {e}")

    def delete_order(self):
        selected = self.table_orders.currentRow()
        if selected < 0:
            return
        try:
            order_id = self.table_orders.item(selected, 0).text()
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            self.load_orders_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить заказ: {e}")


class AppController:
    """Управление окнами приложения"""

    def __init__(self):
        self.stacked_widget = QStackedWidget()
        self.show_login_window()
        self.stacked_widget.show()

    def show_login_window(self):
        self.login_window = LoginWindow(self.switch_to_main)
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.setCurrentWidget(self.login_window)

    def switch_to_main(self, role):
        # ГАРАНТИРОВАННОЕ ИЗВЛЕЧЕНИЕ: очищаем сырой текст SQLite-кортежа от лишних символов
        clean_role = str(role).replace("(", "").replace(")", "").replace("'", "").replace(",", "").strip().lower()

        self.main_window = MainWindow(clean_role, self.logout)
        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.setCurrentWidget(self.main_window)

    def logout(self):
        self.show_login_window()

    style_sheet = """
        * {
            font-family: 'Calibri';
            font-size: 14px;
        }
        QWidget {
            background-color: #FFFFFF; /* Основной фон */
        }
        QLineEdit, QComboBox, QTableWidget, QListWidget {
            background-color: #FFFFFF;
            border: 1px solid #70B2AF;
            border-radius: 4px;
            padding: 5px;
        }
        QPushButton {
            background-color: #D2F6E7; /* Дополнительный фон */
            border: 1px solid #70B2AF;
            border-radius: 5px;
            padding: 6px 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #70B2AF;
            color: white;
        }
        /* Акцентирование внимания на главном действии */
        QPushButton#btn_accent {
            background-color: #70B2AF;
            color: white;
        }
        QPushButton#btn_accent:hover {
            background-color: #599693;
        }
    """

def upgrade_database():
    conn = sqlite3.connect("database/shoes_shop.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE shoes ADD COLUMN category TEXT DEFAULT 'Обувь'")
        cursor.execute("ALTER TABLE shoes ADD COLUMN composition TEXT DEFAULT 'Натуральная кожа'")
        cursor.execute("ALTER TABLE shoes ADD COLUMN image_path TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN order_date TEXT DEFAULT (date('now'))")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # 1. Сначала обновляем базу данных
    upgrade_database()

    # 2. Создаем приложение
    app = QApplication(sys.argv)

    # 3. Объявляем стили (ОБЯЗАТЕЛЬНО возвращаем этот блок!)
    style_sheet = """
        * {
            font-family: 'Calibri', 'Arial';
            font-size: 14px;
        }
        /* Основной фон приложения — белый */
        QWidget {
            background-color: #FFFFFF;
            color: #000000;
        }
        /* Поля ввода и выпадающие списки */
        QLineEdit, QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #70B2AF;
            border-radius: 4px;
            padding: 6px;
        }
        /* Вкладки */
        QTabWidget::pane {
            border: 1px solid #70B2AF;
        }
        QTabBar::tab {
            background-color: #D2F6E7; /* Дополнительный фон */
            border: 1px solid #70B2AF;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #FFFFFF;
            border-bottom-color: #FFFFFF;
        }
        /* Кнопки */
        QPushButton {
            background-color: #D2F6E7;
            border: 1px solid #70B2AF;
            border-radius: 4px;
            padding: 6px 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #70B2AF;
            color: #FFFFFF;
        }
        /* Таблицы */
        QTableWidget {
            gridline-color: #70B2AF;
            border: 1px solid #70B2AF;
        }
        QHeaderView::section {
            background-color: #D2F6E7;
            border: 1px solid #70B2AF;
            padding: 4px;
            font-weight: bold;
        }
        QListWidget::item:selected {
            border: 2px solid #70B2AF; /* Вокруг выбранной карточки появится жирная рамка */
        }
    """

    # 4. Передаем стили в объект приложения
    app.setStyleSheet(style_sheet)

    # 5. Запускаем контроллер окон
    controller = AppController()

    # 6. Самая последняя строчка в файле — держит программу открытой
    sys.exit(app.exec())



