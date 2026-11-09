import math
from PIL import Image


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Вычисляет яркость одного пикселя из его R, G и B.
# Нужна для статистики, профиля, карты контрастности и поиска особенностей.
def intensity(rgb):
    #  I = (R + G + B) / 3
    return (rgb[0] + rgb[1] + rgb[2]) / 3


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Оставляет значение в пределах 0…255 и округляет его до целого.
# Нужна при записи вычисленного значения в пиксель изображения.
def limit(value):
    # Диапазон 8 бит: 0…255
    return round(max(0, min(255, value)))


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Находит среднее, дисперсию и стандартное отклонение.
# Нужна для оценки яркости и её разброса в выбранном окне.
def statistics(values):
    total = 0
    for value in values:
        total += value
    # Среднее: mean = сумма яркостей / количество значений
    mean = total / len(values)
    variance = 0
    # Дисперсия: D = сумма((I - mean) ** 2) / количество значений
    for value in values:
        variance += (value - mean) ** 2
    variance /= len(values)
    # Стандартное отклонение: sigma = корень из D = D ** 0.5
    return mean, variance, variance ** 0.5


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Собирает координаты центра и соседних пикселей для локальных операций.
# Нужна для статистики окна, старого размытия и карты контрастности.
def neighbors(x, y, width, height, kind, size=3):
    points = []
    radius = size // 2
    if kind != "Окно":
        radius = 1
    # На краю берём существующие точки
    for ny in range(max(0, y - radius), min(height, y + radius + 1)):
        for nx in range(max(0, x - radius), min(width, x + radius + 1)):
            if kind != "4" or nx == x or ny == y:
                points.append((nx, ny))
    return points


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Собирает яркости и три гистограммы окна 11×11 вокруг выбранного пикселя.
# Возвращает RGB центра, его яркость, статистику окна, число точек и гистограммы.
def window_statistics(source, x, y):
    values = []
    histograms = [[0] * 256, [0] * 256, [0] * 256]
    for nx, ny in neighbors(x, y, source.width, source.height, "Окно", 11):
        rgb = source.getpixel((nx, ny))
        values.append(intensity(rgb))
        for c in range(3):
            # Абсолютная частота H(u) = число пикселей со значением u
            histograms[c][rgb[c]] += 1
    mean, variance, deviation = statistics(values)
    rgb = source.getpixel((x, y))
    return rgb, intensity(rgb), mean, variance, deviation, len(values), histograms


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Выполняет выбранное редактирование и возвращает новую картинку.
# Нужна для яркости, контраста, негатива, обмена каналов и других старых операций.
def transform(source, operation, channel, value):
    width, height = source.size
    result = Image.new("RGB", source.size)
    pixels, output = source.load(), result.load()
    means = [0, 0, 0]
    if operation == "Контрастность":
        for y in range(height):
            for x in range(width):
                for c in range(3):
                    means[c] += pixels[x, y][c]
        # Среднее каждого канала: сумма его значений / (ширина * высота). 
        for c in range(3):
            means[c] /= width * height
    for y in range(height):
        for x in range(width):
            rgb = list(pixels[x, y])
            if operation == "Отражение слева направо":
                # x' = width - 1 - x: отражение x' = -x и перенос на width - 1.
                rgb = pixels[width - 1 - x, y]
            elif operation == "Отражение сверху вниз":
                # y' = height - 1 - y: отражение y' = -y и перенос на height - 1.
                rgb = pixels[x, height - 1 - y]
            elif operation == "Обмен R и G":
                rgb = [rgb[1], rgb[0], rgb[2]]
            elif operation == "Обмен R и B":
                rgb = [rgb[2], rgb[1], rgb[0]]
            elif operation == "Обмен G и B":
                rgb = [rgb[0], rgb[2], rgb[1]]
            elif operation in ("Размытие: 4 соседа", "Размытие: 8 соседей"):
                kind = "4"
                if operation == "Размытие: 8 соседей":
                    kind = "8"
                points = neighbors(x, y, width, height, kind)
                rgb = [0, 0, 0]
                for nx, ny in points:
                    for c in range(3):
                        rgb[c] += pixels[nx, ny][c]
                # Размытие: новое = сумма значений центра и соседей / число этих точек.
                for c in range(3):
                    rgb[c] = limit(rgb[c] / len(points))
            elif operation == "Бинаризация (своя идея)":
                # Бинаризация: 0 при I < порога, 255 при I >= порога. 
                level = 0
                if intensity(rgb) >= value:
                    level = 255
                rgb = [level, level, level]
            else:
                for c in range(3):
                    if channel != "Все" and channel != "RGB"[c]:
                        continue
                    if operation == "Яркость":
                        rgb[c] = limit(rgb[c] + value)
                    elif operation == "Контрастность":
                        # Контраст: новое = mean + k * (старое - mean), где k = value.
                        rgb[c] = limit(means[c] + value * (rgb[c] - means[c]))
                    elif operation == "Негатив":
                        # Негатив: новое = Gmax - старое, здесь Gmax = 255.
                        rgb[c] = 255 - rgb[c]
            output[x, y] = tuple(rgb)
    return result


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Создаёт серую картинку из средней яркости или выбранного канала R, G, B.
# Возвращает эту картинку и гистограмму всех её пикселей.
def representation(source, channel):
    result = Image.new("RGB", source.size)
    histogram = [0] * 256
    for y in range(source.height):
        for x in range(source.width):
            rgb = source.getpixel((x, y))
            if channel == "Ч/б":
                # Серый уровень = round((R + G + B) / 3), по формуле интенсивности из задания
                value = limit(intensity(rgb))
            else:
                # Каждый RGB-канал - отдельная полутоновая картинка.
                value = rgb["RGB".index(channel)]
            # H(u) = число пикселей со значением u. 
            histogram[value] += 1
            result.putpixel((x, y), (value, value, value))
    return result, histogram


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Собирает яркости пикселей выбранной строки слева направо.
# Полученный список нужен для построения профиля яркости.
def profile(source, y):
    values = []
    for x in range(source.width):
        # Профиль строки: P(x) = I(x, y), где I = (R + G + B) / 3. 
        values.append(intensity(source.getpixel((x, y))))
    return values


# ЛАБА 2 — функция из предыдущей лабораторной, без изменений.
# Сравнивает яркость каждого пикселя со средним его соседей.
# Возвращает серую карту: чем сильнее различие, тем светлее точка.
def contrast_map(source, kind, size):
    gray = []
    for y in range(source.height):
        gray.append(profile(source, y))
    result = Image.new("RGB", source.size)
    for y in range(source.height):
        for x in range(source.width):
            total, count = 0, 0
            for nx, ny in neighbors(x, y, source.width, source.height, kind, size):
                # Сам центр исключаем: здесь нужны только соседние пиксели
                if nx != x or ny != y:
                    total += gray[ny][nx]
                    count += 1
            value = 0
            if count > 0:
                # Карта K(p) = |I(p) - среднее соседей| = |I(p) - total / count|.
                value = limit(abs(gray[y][x] - total / count))
            result.putpixel((x, y), (value, value, value))
    return result


# ЛАБА 4 — новая функция.
# Возвращает одну из учебных матриц для размытия, производных или проверки.
# Гаусс вычисляется по лекции 3, с. 26–27; остальные веса заданы явно.
def make_kernel(name):
    if name == "Усреднение 3×3":
        return [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    if name == "Собель X":
        return [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    if name == "Собель Y":
        return [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    if name == "Единичная 3×3":
        return [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    if name == "Гаусс 5×5":
        # Гаусс: w(x,y) = exp(-(x²+y²)/(2*sigma²)), sigma = 1, окно 5×5.
        # Общий множитель 1/(2*pi*sigma²) сокращается при делении на сумму весов.
        kernel = []
        for y in range(-2, 3):
            row = []
            for x in range(-2, 3):
                row.append(math.exp(-(x * x + y * y) / 2))
            kernel.append(row)
        return kernel
    raise ValueError("Неизвестная матрица фильтра: " + name)


# ЛАБА 4 — новая функция.
# Вычисляет свёртку по каждому каналу, возвращая строки дробных RGB-значений.
# Нужна всем новым фильтрам: знак и дробная часть здесь не теряются.
def convolution(source, kernel, normalize=False, grayscale=False):
    width, height = source.size
    size = len(kernel)
    # 1. Без нормализации делим на 1; с нормализацией — на сумму весов.
    scale = 1.0
    if normalize:
        scale = 0.0
        for row in kernel:
            for weight in row:
                scale += weight
        # Лекция 3, с. 22: S > 0; для усреднения S = сумма весов.
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("Нормализация требует положительной суммы весов. Отключите её или измените матрицу.")
    pixels = source.load()
    result = []
    # Якорь — элемент [size//2][size//2]. При размере 2 смещения равны -1, 0.
    # При размере 4 смещения равны -2, -1, 0, 1; это правило действует по обеим осям.
    radius = size // 2
    # 2. Для каждого пикселя отдельно собираем взвешенную сумму его окна.
    for y in range(height):
        row = []
        for x in range(width):
            total = [0.0, 0.0, 0.0]
            for ky in range(size):
                # На краю повторяем ближайший пиксель, сохраняя все веса ядра.
                ny = y + ky - radius
                if ny < 0:
                    ny = 0
                elif ny >= height:
                    ny = height - 1
                for kx in range(size):
                    nx = x + kx - radius
                    if nx < 0:
                        nx = 0
                    elif nx >= width:
                        nx = width - 1
                    rgb = pixels[nx, ny]
                    if grayscale:
                        # Собелю нужна яркость, а цветным фильтрам — отдельные RGB-каналы.
                        value = intensity(rgb)
                        rgb = (value, value, value)
                    weight = kernel[ky][kx]
                    for c in range(3):
                        # J(x,y) = сумма(w[ky][kx] * I(x+dx,y+dy)) / S.
                        # Лекция 3, с. 22: ядро используется в записанном порядке.
                        total[c] += weight * rgb[c]
            # 3. Делим готовую сумму на S. Округлять и обрезать её ещё нельзя.
            for c in range(3):
                total[c] /= scale
            row.append(total)
        result.append(row)
    return result


# ЛАБА 4 — новая функция.
# Переводит дробные результаты фильтра в RGB-картинку для показа и сохранения.
# Только здесь прибавляем сдвиг, ограничиваем диапазон и округляем.
def values_image(values, shift=0):
    result = Image.new("RGB", (len(values[0]), len(values)))
    output = result.load()
    for y in range(result.height):
        for x in range(result.width):
            rgb = []
            for c in range(3):
                # Для показа: round(max(0, min(255, J + shift))).
                rgb.append(limit(values[y][x][c] + shift))
            output[x, y] = tuple(rgb)
    return result


# ЛАБА 4 — новая функция.
# Вычитает размытое изображение с коэффициентом c, выделяя быстрые изменения.
# Использует формулу задания 4, а +128 позволяет показать отрицательные значения.
def high_pass(source, kernel, coefficient):
    # Сначала result содержит размытие, затем заменяем его значениями High-pass.
    result = convolution(source, kernel, True)
    pixels = source.load()
    for y in range(source.height):
        for x in range(source.width):
            for c in range(3):
                # ВЧ = ИСХ - РАЗМ * c. Размытые значения ещё не округлены.
                result[y][x][c] = pixels[x, y][c] - result[y][x][c] * coefficient
    return values_image(result, 128)


# ЛАБА 4 — новая функция.
# Выделяет границы по Собелю из лекции 3, с. 34.
# Складывает модули двух производных и показывает их серой картой.
def sobel(source):
    sx = convolution(source, make_kernel("Собель X"), False, True)
    sy = convolution(source, make_kernel("Собель Y"), False, True)
    for y in range(source.height):
        for x in range(source.width):
            # G = |Sx| + |Sy|; до взятия модуля знак производных сохранён.
            value = abs(sx[y][x][0]) + abs(sy[y][x][0])
            sx[y][x] = [value, value, value]
    return values_image(sx)


# ЛАБА 4 — новая функция.
# Находит углы FAST-9 по лекции 4, с. 25, и отмечает их красными точками.
# Проверяет 9 подряд ярких или тёмных соседей на замкнутой окружности радиуса 3.
def fast_corners(source, threshold):
    gray = []
    for y in range(source.height):
        gray.append(profile(source, y))
    circle = [(0, -3), (1, -3), (2, -2), (3, -1),
              (3, 0), (3, 1), (2, 2), (1, 3),
              (0, 3), (-1, 3), (-2, 2), (-3, 1),
              (-3, 0), (-3, -1), (-2, -2), (-1, -3)]
    # 16 точек + повтор первых 8: так проверяются и серии через конец списка.
    for i in range(8):
        circle.append(circle[i])
    result = source.copy()
    # Пропускаем полосу шириной 3: для FAST нужна вся окружность внутри картинки.
    for y in range(3, source.height - 3):
        for x in range(3, source.width - 3):
            center = gray[y][x]
            # Счётчики показывают, сколько ярких или тёмных точек идут подряд.
            bright = 0
            dark = 0
            for dx, dy in circle:
                value = gray[y + dy][x + dx]
                if value > center + threshold:
                    bright += 1
                else:
                    # Если серия прервалась, начинаем считать заново.
                    bright = 0
                if value < center - threshold:
                    dark += 1
                else:
                    dark = 0
                if bright >= 9 or dark >= 9:
                    # Красная точка 3×3; яркости для теста берутся только из gray.
                    for ny in range(y - 1, y + 2):
                        for nx in range(x - 1, x + 2):
                            result.putpixel((nx, ny), (255, 0, 0))
                    break
    return result
