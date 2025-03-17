import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from matplotlib.widgets import Slider
from datetime import datetime

# Чтение данных из CSV файла
data = pd.read_csv('./results/2024-11-10 08-04_optimization_2024-10_MomentumVWMA.csv')

parameter1 = 'momentum_period'
parameter2 = 'vwma_period'

# Извлечение необходимых колонок для построения графика
x = data[parameter1]  # по оси X
y = data[parameter2]  # по оси Y
z = data['pnl net']  # по оси Z (PNL net)

# Создание 3D-графика
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Построение поверхности с использованием триангуляции
surf = ax.plot_trisurf(x, y, z, cmap='viridis', edgecolor='none')

# Подписи к осям
ax.set_xlabel(parameter1)
ax.set_ylabel(parameter2)
ax.set_zlabel('PNL Net')

# Заголовок графика
current_time = datetime.now().strftime("%Y-%m-%d %H:%M") # Генерируем текущее время в формате 'yyyy-mm-dd HH:mm'
ax.set_title(f"3D Optimization Chart, {current_time}")

# Добавление плоскости, которая будет двигаться вдоль оси Z
# Начальное значение плоскости по оси Z
z_plane = np.mean(z)

# Плоскость - запоминаем ее как отдельный объект
x_plane = np.array([[min(x), max(x)], [min(x), max(x)]])
y_plane = np.array([[min(y), min(y)], [max(y), max(y)]])
z_plane_values = np.array([[z_plane, z_plane], [z_plane, z_plane]])

# Отображение плоскости
plane = ax.plot_surface(x_plane, y_plane, z_plane_values, color='red', alpha=0.5)

# Создание слайдера для управления позицией плоскости по оси Z
ax_slider = plt.axes([0.25, 0.02, 0.50, 0.03], facecolor='lightgoldenrodyellow')
z_slider = Slider(ax_slider, 'Z Plane', min(z), max(z), valinit=z_plane)

# Функция обновления положения плоскости при перемещении слайдера
def update(val):
    new_z_plane = z_slider.val
    z_plane_values[:] = new_z_plane  # Обновляем значения Z для плоскости
    ax.collections[-1].remove()  # Удаляем старую плоскость
    ax.plot_surface(x_plane, y_plane, z_plane_values, color='red', alpha=0.5)  # Рисуем новую плоскость
    fig.canvas.draw_idle()  # Обновляем график

# Привязка слайдера к функции обновления
z_slider.on_changed(update)

# # Добавление текста рядом с графиком с использованием ax.text
# text = """На периоде 2024-05 \n
#         часовая цена ниже часовой скользящей средней \n 
#         ma_period_5min=range(5, 60, 10),\n 
#         ma_period_hourly=range(30, 60, 5),\n
#         trailing_stop=[0.05]"""
# ax.text(1.05, 0.5, 0.5, text, fontsize=10, color='black', transform=ax.transAxes)

# Отображение графика
plt.show()
