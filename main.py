import tkinter as tk
import math
from tkinter import filedialog, messagebox, ttk
from functools import partial
from pathlib import Path
from PIL import Image, ImageTk
import algorithms as alg


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт область для картинки и возвращает её.
# При изменении размера области картинка автоматически подгоняется под неё.
def image_canvas(parent, picture=None):
    view = tk.Canvas(parent, background="#20262c", highlightthickness=0, width=500, height=300)
    view.pack(fill="both", expand=True)
    view.picture, view.selected = picture, None
    view.bind("<Configure>", partial(fit_image, view))
    return view


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Подгоняет картинку под доступное место и рисует её без обрезания.
# В рабочей области обновляет статистику; рамку показывает только под мышью.
def fit_image(view, event=None):
    view.delete("all")
    if view.picture is None:
        view.create_text(view.winfo_width() / 2, view.winfo_height() / 2,
                         text="Откройте изображение PNG, BMP или TIFF", fill="#aeb8c4")
        return
    picture = view.picture
    space_w, space_h = max(1, view.winfo_width() - 20), max(1, view.winfo_height() - 20)
    # Масштаб: s = min(ширина области / ширина картинки, высота области / высота картинки).
    # Это правило вписывания в область, а не отдельная формула из лекций.
    scale = min(space_w / picture.width, space_h / picture.height)
    width, height = max(1, round(picture.width * scale)), max(1, round(picture.height * scale))
    view.display = (width, height)
    view.offset = ((view.winfo_width() - width) / 2, (view.winfo_height() - height) / 2)
    method = Image.Resampling.LANCZOS
    if scale >= 1:
        method = Image.Resampling.NEAREST
    view.photo = ImageTk.PhotoImage(picture.resize((width, height), method))
    view.create_image(*view.offset, anchor="nw", image=view.photo)
    if view == canvas and view.selected is not None:
        # Проверяем настоящее положение мыши: после изменения окна картинка могла сместиться.
        mouse_x = view.winfo_pointerx() - view.winfo_rootx()
        mouse_y = view.winfo_pointery() - view.winfo_rooty()
        ox, oy = view.offset
        if ox <= mouse_x < ox + width and oy <= mouse_y < oy + height:
            # Обратный масштаб: x = (экранный x - отступ) * ширина картинки / ширина показа.
            # Это пересчёт координат для интерфейса, а не формула обработки из лекций.
            update_pixel(int((mouse_x - ox) * picture.width / width),
                         int((mouse_y - oy) * picture.height / height))
        else:
            update_pixel(*view.selected)
            view.delete("window")


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт область для гистограммы или профиля яркости и возвращает её.
# Сохраняет данные графика, чтобы его можно было перерисовать при изменении размера.
def graph_canvas(parent, values, color, histogram=True):
    chart = tk.Canvas(parent, height=125, width=180, background="#f8fafc",
                      highlightbackground="#dce1e7", highlightthickness=1)
    chart.pack(fill="both", expand=True)
    chart.values, chart.color, chart.histogram = values, color, histogram
    chart.bind("<Configure>", partial(draw_graph, chart))
    return chart


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Рисует сохранённые значения: столбики для гистограммы или линию для профиля.
# Подгоняет график и подписи осей под текущий размер области.
def draw_graph(chart, event=None):
    chart.delete("all")
    width, height = max(50, chart.winfo_width()), max(50, chart.winfo_height())
    peak = 255
    if chart.histogram:
        peak = max(1, max(chart.values))
    left, bottom = 27, height - 20
    chart.create_line(left, 10, left, bottom, width - 8, bottom, fill="#cbd2db")
    chart.create_text(3, 12, anchor="w", text=str(peak), fill="#788493", font=("Segoe UI", 8))
    chart.create_text(left, height - 8, text="0", fill="#788493", font=("Segoe UI", 8))
    chart.create_text(width - 17, height - 8, text=str(len(chart.values) - 1), fill="#788493", font=("Segoe UI", 8))
    previous = None
    for i in range(len(chart.values)):
        # Доля значения умножается на размер графика: так получаем экранные x и y.
        # Это правило рисования графика; отдельной формулы в лекциях нет.
        x = left + (width - left - 10) * i / max(1, len(chart.values) - 1)
        y = bottom - (bottom - 12) * chart.values[i] / peak
        if chart.histogram:
            chart.create_line(x, bottom, x, y, fill=chart.color, width=2)
        elif previous is None:
            chart.create_oval(x - 2, y - 2, x + 2, y + 2, fill=chart.color)
        else:
            chart.create_line(previous[0], previous[1], x, y, fill=chart.color)
        previous = (x, y)

# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Показывает текущую картинку, её размеры и статистику выбранного пикселя.
# Сразу после загрузки выбирает середину картинки, чтобы поля не оставались пустыми.
def show_image():
    canvas.picture = image
    dimensions.set(f"{image.width} × {image.height} px")
    if canvas.selected is None:
        canvas.selected = (image.width // 2, image.height // 2)
    fit_image(canvas)


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Загружает картинку, переводит её в RGB и сохраняет отдельную исходную копию.
# Если путь не передан, сначала открывает окно выбора; неподдерживаемый файл отклоняет.
def open_image(path=None):
    global image, original
    if path is None:
        path = filedialog.askopenfilename(filetypes=[("Изображения без потерь", "*.png *.bmp *.tif *.tiff")])
    if not path:
        return
    try:
        with Image.open(path) as loaded:
            if loaded.format not in ("PNG", "BMP", "TIFF"):
                raise ValueError("Поддерживаются изображения PNG, BMP и TIFF.")
            # Обычные картинки с палитрой, оттенками серого или прозрачностью тоже переводим в RGB.
            if loaded.mode not in ("RGB", "RGBA", "P", "L", "LA", "1"):
                raise ValueError("Поддерживаются изображения с точностью не выше 8 бит на канал.")
            # TIFF: поле 258 хранит разрядность каналов, даже если Pillow уже показывает режим RGB.
            if loaded.format == "TIFF":
                for bits in loaded.tag_v2.get(258, (1,)):
                    if bits > 8:
                        raise ValueError("TIFF с точностью выше 8 бит на канал не поддерживается.")
            # PNG: байт с номером 24 в заголовке хранит число бит на канал.
            if loaded.format == "PNG":
                position = loaded.fp.tell()
                loaded.fp.seek(24)
                bits = loaded.fp.read(1)
                loaded.fp.seek(position)
                if bits == b"\x10":
                    raise ValueError("16-битный PNG не поддерживается. Выберите 8-битное изображение.")
            image = loaded.convert("RGB")
        original = image.copy()
        canvas.selected = None
        show_image()
    except (OSError, ValueError) as error:
        messagebox.showerror("Ошибка загрузки", str(error))


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Открывает окно выбора места и сохраняет текущий результат в PNG, BMP или TIFF.
# При ошибке записи показывает сообщение, чтобы пользователь знал, что файл не сохранён.
def save_image():
    if image is None:
        return
    path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[
        ("PNG", "*.png"), ("BMP", "*.bmp"), ("TIFF", "*.tiff")])
    if path:
        try:
            image.save(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка сохранения", str(error))


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Восстанавливает сохранённую исходную копию и показывает её.
# Так можно отменить сразу все изменения текущей картинки.
def reset_image():
    global image
    if original is not None:
        image = original.copy()
        show_image()


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Находит пиксель под мышью и обновляет рамку, числа и гистограммы.
# Вне картинки убирает рамку; при щелчке выбирает строку для профиля.
def mouse(event):
    canvas.delete("window")
    if image is None or event.type == tk.EventType.Leave:
        return
    width, height = canvas.display
    ox, oy = canvas.offset
    if not (ox <= event.x < ox + width and oy <= event.y < oy + height):
        return
    # Обратный масштаб: координата пикселя = (координата мыши - отступ) * исходный размер / размер показа.
    # Пересчёт нужен для интерфейса; 
    x = int((event.x - ox) * image.width / width)
    y = int((event.y - oy) * image.height / height)
    update_pixel(x, y)
    if event.type == tk.EventType.ButtonPress:
        inputs["row"].set(str(y))

# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Получает статистику выбранного пикселя и окна 11×11, выводит числа и RGB-гистограммы.
# Рисует внешнюю рамку вокруг выбранного окна.
def update_pixel(x, y):
    canvas.selected = (x, y)
    rgb, level, mean, variance, deviation, count, histograms = alg.window_statistics(image, x, y)
    values = [f"({x}, {y})", f"{rgb[0]}, {rgb[1]}, {rgb[2]}", f"{level:.2f}",
              f"{mean:.2f}", f"{variance:.2f}", f"{deviation:.2f}", str(count)]
    for i in range(len(fields)):
        fields[i].set(values[i])
    for c in range(3):
        charts[c].values = histograms[c]
        draw_graph(charts[c])
    ox, oy = canvas.offset
    sx, sy = canvas.display[0] / image.width, canvas.display[1] / image.height
    canvas.delete("window")
    # По практическому заданию внешняя рамка имеет размер 13×13: от x-6 до x+7, аналогично по y.
    # Это границы 13 ячеек вокруг центра выбранного пикселя; sx и sy переводят их в экранные размеры.
    canvas.create_rectangle(ox + (x - 6) * sx, oy + (y - 6) * sy,
                            ox + (x + 7) * sx, oy + (y + 7) * sy,
                            outline="#f9dc45", width=1, tags="window")


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Проверяет параметр выбранной операции и передаёт картинку в algorithms.py.
# Заменяет текущую картинку результатом и обновляет рабочую область.
def apply_operation(operation=None, channel="Все", value=0):
    global image
    if image is None:
        return
    if operation is None:
        operation = inputs["operation"].get()
        channel = inputs["channel"].get()
        value = inputs["value"].get()
    if operation == "Бинаризация (своя идея)":
        value = inputs["threshold"].get()
    try:
        if operation in ("Яркость", "Контрастность", "Бинаризация (своя идея)"):
            value = float(value)
            if not -float("inf") < value < float("inf"):
                raise ValueError
            if operation == "Контрастность" and value < 0:
                raise ValueError
            if operation == "Бинаризация (своя идея)" and not 0 <= value <= 255:
                raise ValueError
    except ValueError:
        messagebox.showerror("Параметр", "Введите конечное число. Контраст ≥ 0; порог от 0 до 255.")
        return
    image = alg.transform(image, operation, channel, value)
    show_image()


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Открывает четыре вкладки: полутона, R, G и B с полными гистограммами.
# Позволяет отдельно рассмотреть составляющие текущей картинки.
def show_views():
    if image is None:
        return
    window = tk.Toplevel(root)
    window.title("Полутона, RGB-каналы и полные гистограммы")
    window.geometry("850x650")
    tabs = ttk.Notebook(window)
    tabs.pack(fill="both", expand=True)
    for name, channel, color in (("Полутона", "Ч/б", "#334155"), ("Красный", "R", "#dc3035"),
                                  ("Зелёный", "G", "#16a34a"), ("Синий", "B", "#2563eb")):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text=name)
        picture, histogram = alg.representation(image, channel)
        bottom = ttk.Frame(frame)
        bottom.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Label(bottom, text="Полная гистограмма: значение → число пикселей").pack(anchor="w")
        graph_canvas(bottom, histogram, color)
        image_canvas(frame, picture)


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Проверяет номер строки и открывает график её яркости.
# Берёт именно исходную картинку, поэтому редактирование не меняет этот профиль.
def show_profile():
    if original is None:
        return
    try:
        y = int(inputs["row"].get())
        if not 0 <= y < original.height:
            raise ValueError
    except ValueError:
        messagebox.showerror("Строка", f"Введите целую строку от 0 до {original.height - 1}.")
        return
    window = tk.Toplevel(root)
    window.title(f"Профиль исходного изображения — строка {y}")
    ttk.Label(window, text="Координата x → интенсивность исходного изображения").pack(pady=8)
    chart = graph_canvas(window, alg.profile(original, y), "#2563eb", False)
    chart.configure(width=650, height=220)

# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Проверяет размер окна и строит карту контрастности выбранным способом.
# Показывает полученную карту вместо текущей картинки.
def apply_map():
    global image
    if image is None:
        return
    size = 3
    if inputs["neighbors"].get() == "Окно":
        try:
            size = int(inputs["size"].get())
            if size < 3 or size % 2 == 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Окно", "Размер должен быть нечётным целым числом ≥ 3.")
            return
    image = alg.contrast_map(image, inputs["neighbors"].get(), size)
    show_image()


# ЛАБА 4 — новая функция.
# Читает квадратную матрицу из текста; размер определяет по числу элементов.
# Запятые, пробелы и переносы строк служат одинаковыми разделителями.
def parse_kernel(text):
    numbers = text.replace(",", " ").split()
    size = math.isqrt(len(numbers))
    if size == 0 or size * size != len(numbers):
        raise ValueError("Введите n×n чисел: например, 4, 9, 16 или 25. Поле не должно быть пустым.")
    kernel = []
    for y in range(size):
        row = []
        for x in range(size):
            try:
                value = float(numbers[y * size + x])
            except ValueError:
                raise ValueError("В матрице должны быть числа. Дробную часть отделяйте точкой.") from None
            if not math.isfinite(value):
                raise ValueError("Все веса матрицы должны быть конечными числами.")
            row.append(value)
        kernel.append(row)
    return kernel


# ЛАБА 4 — новая функция.
# Заполняет редактируемое поле выбранной готовой матрицей.
# Для Собеля сразу отключает нормализацию, так как сумма его весов равна нулю.
def load_kernel(event=None):
    name = inputs["kernel"].get()
    kernel = alg.make_kernel(name)
    kernel_text.delete("1.0", "end")
    for row in kernel:
        numbers = []
        for weight in row:
            numbers.append(str(weight))
        kernel_text.insert("end", " ".join(numbers) + "\n")
    inputs["normalize"].set(name not in ("Собель X", "Собель Y"))


# ЛАБА 4 — новая функция.
# Проверяет поля новых операций, вызывает алгоритм и показывает результат.
# Размытие и High-pass берут original; остальные фильтры — текущую картинку.
def apply_filter(operation):
    global image
    if image is None:
        return
    try:
        if operation in ("High-pass", "FAST"):
            key, label = "coefficient", "Коэффициент c"
            if operation == "FAST":
                key, label = "fast_threshold", "Порог FAST"
            try:
                value = float(inputs[key].get())
            except ValueError:
                raise ValueError(label + ": введите число с точкой в дробной части.") from None
            if not math.isfinite(value):
                raise ValueError(label + ": введите конечное число.")
            if operation == "FAST" and not 0 <= value <= 255:
                raise ValueError("Порог FAST должен быть от 0 до 255.")
        if operation in ("Размытие", "High-pass"):
            kernel = alg.make_kernel(inputs["blur"].get())
            if operation == "Размытие":
                result = alg.values_image(alg.convolution(original, kernel, True))
            else:
                result = alg.high_pass(original, kernel, value)
        elif operation == "Свёртка":
            kernel = parse_kernel(kernel_text.get("1.0", "end"))
            shift = 0
            if inputs["shift"].get():
                shift = 128
            values = alg.convolution(image, kernel, inputs["normalize"].get())
            result = alg.values_image(values, shift)
        elif operation == "FAST":
            result = alg.fast_corners(image, value)
        else:
            result = alg.sobel(image)
    except (ValueError, OverflowError) as error:
        messagebox.showerror("Параметры фильтра", str(error))
        return
    image = result
    show_image()


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Загружает учебную картинку с однородным и неоднородным участками.
# Показывает, какие средние и дисперсии можно проверить наведением мыши.
def show_examples():
    open_image(Path(__file__).with_name("example.png"))
    messagebox.showinfo("Примеры однородности",
        "(64, 64): однородная область, среднее 128, дисперсия 0.\n"
        "(192, 64): неоднородная, среднее ≈127.21, дисперсия ≈9215.37.\n\n"
        "У однородной области гистограмма узкая, у неоднородной — разброс значений.")

# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт карточку с заголовком в правой панели и возвращает её.
# Внутрь карточки затем добавляются нужные поля и кнопки.
def section(parent, title):
    frame = ttk.Frame(parent, style="Card.TFrame", padding=16)
    frame.pack(fill="x", pady=(0, 12))
    ttk.Label(frame, text=title, style="Section.TLabel").pack(anchor="w", pady=(0, 12))
    return frame


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт и возвращает пустую строку интерфейса.
# Она нужна для размещения нескольких элементов рядом.
def line(parent):
    row = ttk.Frame(parent)
    row.pack(fill="x", pady=4)
    return row


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Размещает переданные кнопки в одну строку одинаковой ширины.
# Каждая кнопка запускает переданную вместе с её названием команду.
def button_row(parent, buttons):
    row = line(parent)
    for text, command in buttons:
        ttk.Button(row, text=text, command=command).pack(side="left", fill="x", expand=True, padx=2)


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт строки статистики: слева название, справа изменяемое значение.
# Сохраняет переменные этих значений в fields для последующего обновления.
def info_rows(parent, names):
    for name in names:
        row = line(parent)
        fields.append(tk.StringVar(value="—"))
        ttk.Label(row, text=name, style="Muted.TLabel").pack(side="left")
        ttk.Label(row, textvariable=fields[-1]).pack(side="right")


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Подгоняет содержимое правой панели под её ширину и обновляет границы прокрутки.
# После изменения окна все карточки остаются доступными через полосу прокрутки.
def resize_sidebar(event):
    if event.widget == sidebar:
        sidebar.itemconfigure("panel", width=event.width)
    sidebar.configure(scrollregion=sidebar.bbox("all"))


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Прокручивает правую панель колёсиком, только если указатель находится над ней.
# Проверяет также вложенные кнопки и поля, поднимаясь к их родительским элементам.
def scroll_sidebar(event):
    widget = root.winfo_containing(event.x_root, event.y_root)
    while widget is not None:
        if widget == sidebar:
            sidebar.yview_scroll(-1 if event.delta > 0 else 1, "units")
            break
        widget = widget.master


# ЛАБА 2 + 4 — функция была в лабораторной №2,
# но дополнена для выполнения лабораторной №4.
# Создаёт главное окно, оформление, рабочую область, графики и правую панель.
# Связывает кнопки с функциями и запускает ожидание действий пользователя.
def start():
    # ЛАБА 4: к общим переменным добавлено поле матрицы kernel_text.
    global root, canvas, sidebar, dimensions, charts, fields, inputs, kernel_text
    root = tk.Tk()
    # ЛАБА 4: новое название окна.
    root.title("Практическое задание 4 — Фильтры, углы и границы")
    root.geometry(f"{min(1400, root.winfo_screenwidth() - 80)}x{min(900, root.winfo_screenheight() - 100)}")
    root.minsize(900, 600)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10))
    style.configure("TFrame", background="white")
    style.configure("Background.TFrame", background="#f3f4f6")
    style.configure("Card.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#d9dde3")
    style.configure("TLabel", background="white", foreground="#26313d")
    style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"))
    style.configure("Muted.TLabel", foreground="#7a8490", font=("Segoe UI", 9))
    style.configure("TButton", padding=8, background="#e6e8eb")
    style.configure("Accent.TButton", background="#2563eb", foreground="white", padding=(22, 10))
    header = ttk.Frame(root, padding=(24, 14))
    header.pack(fill="x")
    title = ttk.Frame(header)
    title.pack(side="left")
    # ЛАБА 4: новые подписи в шапке окна.
    ttk.Label(title, text="Обработка изображений", style="Title.TLabel").pack(anchor="w")
    ttk.Label(title, text="Практическое задание 4", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
    for text, command in (("Сбросить", reset_image), ("Сохранить", save_image), ("Открыть", open_image)):
        ttk.Button(header, text=text, command=command,
                   style="Accent.TButton" if text == "Открыть" else "TButton").pack(side="right", padx=4)
    body = ttk.Frame(root, style="Background.TFrame", padding=12)
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)
    left = ttk.Frame(body, style="Background.TFrame")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    bottom = ttk.Frame(left, style="Card.TFrame", padding=16)
    bottom.pack(side="bottom", fill="x", pady=(10, 0))
    ttk.Label(bottom, text="Гистограммы текущего окна 11 × 11", style="Section.TLabel").pack(anchor="w")
    row = ttk.Frame(bottom)
    row.pack(fill="both", expand=True, pady=(6, 0))
    charts, fields = [], []
    for i, (c, color) in enumerate((("R", "#dc3035"), ("G", "#16a34a"), ("B", "#2563eb"))):
        row.columnconfigure(i, weight=1, uniform="histograms")
        column = ttk.Frame(row)
        column.grid(row=0, column=i, sticky="nsew", padx=4)
        ttk.Label(column, text=c, foreground=color).pack(anchor="w", pady=(0, 4))
        charts.append(graph_canvas(column, [0] * 256, color))
    work = ttk.Frame(left, style="Card.TFrame", padding=12)
    work.pack(fill="both", expand=True)
    work_header = line(work)
    ttk.Label(work_header, text="Рабочая область", style="Section.TLabel").pack(side="left")
    dimensions = tk.StringVar(value="Изображение не открыто")
    ttk.Label(work_header, textvariable=dimensions, style="Muted.TLabel").pack(side="right")
    canvas = image_canvas(work)
    canvas.bind("<Motion>", mouse)
    canvas.bind("<Leave>", mouse)
    canvas.bind("<Button-1>", mouse)
    side = ttk.Frame(body, width=340)
    side.grid(row=0, column=1, sticky="ns")
    side.pack_propagate(False)
    sidebar = tk.Canvas(side, background="#f3f4f6", highlightthickness=0, width=320)
    scrollbar = ttk.Scrollbar(side, orient="vertical", command=sidebar.yview)
    scrollbar.pack(side="right", fill="y")
    sidebar.pack(side="left", fill="both", expand=True)
    sidebar.configure(yscrollcommand=scrollbar.set)
    panel = ttk.Frame(sidebar, style="Background.TFrame")
    sidebar.create_window(0, 0, anchor="nw", window=panel, tags="panel")
    panel.bind("<Configure>", resize_sidebar)
    sidebar.bind("<Configure>", resize_sidebar)
    root.bind_all("<MouseWheel>", scroll_sidebar)
    # ЛАБА 4: старые поля inputs перенесены сюда, перед созданием новых кнопок.
    inputs = {}
    for key, value in (("channel", "Все"), ("operation", "Яркость"), ("value", "20"),
                       ("row", "0"), ("neighbors", "4"), ("size", "11"), ("threshold", "128"),
                       # ЛАБА 4: добавлены поля размытия, High-pass, матрицы и FAST.
                       ("blur", "Усреднение 3×3"), ("coefficient", "1"),
                       ("kernel", "Усреднение 3×3"), ("fast_threshold", "20")):
        inputs[key] = tk.StringVar(value=value)
    # ЛАБА 4: начало новых элементов управления — галочки и три раздела фильтров.
    inputs["normalize"] = tk.BooleanVar(value=True)
    inputs["shift"] = tk.BooleanVar(value=False)
    frame = section(panel, "HIGH-PASS")
    ttk.Label(frame, text="Размытие и High-pass от исходного\nизображения. ВЧ = ИСХ − РАЗМ × c.",
              style="Muted.TLabel").pack(anchor="w")
    ttk.Combobox(frame, textvariable=inputs["blur"], values=["Усреднение 3×3", "Гаусс 5×5"],
                 state="readonly").pack(fill="x", pady=6)
    row = line(frame)
    ttk.Label(row, text="Коэффициент c:").pack(side="left")
    ttk.Entry(row, textvariable=inputs["coefficient"], width=8).pack(side="right")
    button_row(frame, [("Размытие", partial(apply_filter, "Размытие")),
                       ("High-pass", partial(apply_filter, "High-pass"))])
    ttk.Label(frame, text="High-pass показан со сдвигом +128.", style="Muted.TLabel").pack(anchor="w")
    frame = section(panel, "СВЁРТКА")
    ttk.Label(frame, text="Фильтр текущего изображения.\nГотовая матрица (заменяет текст):", style="Muted.TLabel").pack(anchor="w")
    choice = ttk.Combobox(frame, textvariable=inputs["kernel"], state="readonly",
                          values=["Усреднение 3×3", "Гаусс 5×5", "Собель X", "Собель Y", "Единичная 3×3"])
    choice.pack(fill="x", pady=6)
    choice.bind("<<ComboboxSelected>>", load_kernel)
    kernel_text = tk.Text(frame, width=25, height=6, wrap="none", font=("Consolas", 10))
    kernel_text.pack(fill="x")
    matrix_scroll = ttk.Scrollbar(frame, orient="horizontal", command=kernel_text.xview)
    matrix_scroll.pack(fill="x")
    kernel_text.configure(xscrollcommand=matrix_scroll.set)
    ttk.Label(frame, text="Своя матрица: n×n чисел, разделители —\nпробел, запятая, новая строка. Дроби: 0.5.\nРазмер определяется по числу значений.",
              style="Muted.TLabel").pack(anchor="w", pady=4)
    row = line(frame)
    ttk.Checkbutton(row, text="Нормализация", variable=inputs["normalize"]).pack(side="left")
    ttk.Checkbutton(row, text="+128", variable=inputs["shift"]).pack(side="right")
    ttk.Label(frame, text="Нормализация: делим на сумму весов > 0.\nЯкорь: [n//2, n//2], нумерация с нуля.\nКрая: повтор ближайшего пикселя.",
              style="Muted.TLabel").pack(anchor="w")
    button_row(frame, [("Применить свёртку", partial(apply_filter, "Свёртка"))])
    load_kernel()
    frame = section(panel, "УГЛЫ И ГРАНИЦЫ")
    ttk.Label(frame, text="Для текущего изображения.", style="Muted.TLabel").pack(anchor="w")
    row = line(frame)
    ttk.Label(row, text="Порог FAST (0…255):").pack(side="left")
    ttk.Entry(row, textvariable=inputs["fast_threshold"], width=7).pack(side="right")
    button_row(frame, [("Углы FAST", partial(apply_filter, "FAST")),
                       ("Границы Собеля", partial(apply_filter, "Собель"))])
    # Конец добавленного блока ЛАБЫ 4. Далее идут прежние разделы ЛАБЫ 2.
    info_rows(section(panel, "ТЕКУЩИЙ ПИКСЕЛЬ"), ["Координаты", "RGB", "Интенсивность"])
    info_rows(section(panel, "ОКНО 11 × 11"), ["Среднее", "Дисперсия", "Стандартное отклонение", "Количество пикселей"])
    frame = section(panel, "ЯРКОСТЬ И КОНТРАСТ")
    # partial заранее запоминает аргументы: сама операция выполнится только после нажатия кнопки.
    button_row(frame, [("Яркость +20", partial(apply_operation, "Яркость", "Все", 20)),
                       ("Яркость −20", partial(apply_operation, "Яркость", "Все", -20))])
    button_row(frame, [("Контраст +", partial(apply_operation, "Контрастность", "Все", 1.25)),
                       ("Контраст −", partial(apply_operation, "Контрастность", "Все", 0.8))])
    button_row(frame, [("Негатив", partial(apply_operation, "Негатив"))])
    frame = section(panel, "ЦВЕТОВЫЕ КАНАЛЫ И ОТРАЖЕНИЕ")
    button_row(frame, [("R +20", partial(apply_operation, "Яркость", "R", 20)),
                       ("G +20", partial(apply_operation, "Яркость", "G", 20)),
                       ("B +20", partial(apply_operation, "Яркость", "B", 20))])
    row = line(frame)
    ttk.Combobox(row, textvariable=inputs["operation"], values=["Яркость", "Контрастность", "Негатив"], state="readonly", width=13).pack(side="left", fill="x", expand=True)
    ttk.Combobox(row, textvariable=inputs["channel"], values=["Все", "R", "G", "B"], state="readonly", width=5).pack(side="left", padx=4)
    ttk.Entry(row, textvariable=inputs["value"], width=6).pack(side="left")
    button_row(frame, [("Применить к выбранным каналам", apply_operation)])
    button_row(frame, [("R ↔ G", partial(apply_operation, "Обмен R и G")),
                       ("R ↔ B", partial(apply_operation, "Обмен R и B")),
                       ("G ↔ B", partial(apply_operation, "Обмен G и B"))])
    button_row(frame, [("Слева направо", partial(apply_operation, "Отражение слева направо")),
                       ("Сверху вниз", partial(apply_operation, "Отражение сверху вниз"))])
    frame = section(panel, "РАЗМЫТИЕ")
    button_row(frame, [("4 соседа", partial(apply_operation, "Размытие: 4 соседа")),
                       ("8 соседей", partial(apply_operation, "Размытие: 8 соседей"))])
    frame = section(panel, "СТАТИСТИКА И КОНТРАСТНОСТЬ")
    ttk.Label(frame, text="Строка исходного изображения", style="Muted.TLabel").pack(anchor="w")
    row = line(frame)
    ttk.Entry(row, textvariable=inputs["row"], width=7).pack(side="left", padx=(0, 8))
    ttk.Button(row, text="Профиль яркости", command=show_profile).pack(side="left", fill="x", expand=True)
    row = line(frame)
    ttk.Label(row, text="Соседство:", style="Muted.TLabel").pack(side="left")
    ttk.Combobox(row, textvariable=inputs["neighbors"], values=["4", "8", "Окно"], state="readonly", width=6).pack(side="left", padx=5)
    ttk.Label(row, text="Размер:", style="Muted.TLabel").pack(side="left")
    ttk.Entry(row, textvariable=inputs["size"], width=5).pack(side="left", padx=5)
    button_row(frame, [("Карта контрастности", apply_map)])
    ttk.Label(frame, text="|Яркость центра − среднее соседей|", style="Muted.TLabel").pack(anchor="w", pady=5)
    button_row(frame, [("Полные гистограммы и RGB", show_views)])
    frame = section(panel, "ДОПОЛНИТЕЛЬНО")
    row = line(frame)
    ttk.Label(row, text="Порог:", style="Muted.TLabel").pack(side="left", padx=(0, 8))
    ttk.Entry(row, textvariable=inputs["threshold"], width=6).pack(side="left")
    ttk.Button(row, text="Бинаризация", command=partial(apply_operation, "Бинаризация (своя идея)")).pack(side="right", fill="x", expand=True, padx=(8, 0))
    button_row(frame, [("Примеры однородности", show_examples)])
    root.mainloop()


image = None
original = None
if __name__ == "__main__":
    start()
