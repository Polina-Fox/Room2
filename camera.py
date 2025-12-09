# -*- coding: utf-8 -*-
"""
Класс камеры с управлением мышью и клавиатурой
"""

import numpy as np
import math

class Camera:
    def __init__(self, width, height):
        """Инициализация камеры"""
        self.width = width      # Ширина окна
        self.height = height    # Высота окна
        
        # ПАРАМЕТРЫ КАМЕРЫ
        self.position = [0.0, 0.0, 20.0]  # Позиция камеры в мире
        self.target = [0.0, 0.0, -1.0]    # Направление взгляда
        self.up = [0.0, 1.0, 0.0]         # Вектор "вверх"
        
        # УГЛЫ ВРАЩЕНИЯ (ЭЙЛЕРА)
        self.yaw = -90.0   # Поворот по горизонтали (рыскание)
        self.pitch = 0.0   # Поворот по вертикали (тангаж)
        
        # ЧУВСТВИТЕЛЬНОСТЬ
        self.rotation_speed = 0.5   # Скорость вращения
        self.pan_speed = 0.01       # Скорость перемещения
        self.zoom_speed = 2.0       # Скорость приближения
        
        # ПАРАМЕТРЫ ПРОЕКЦИИ
        self.fov = 60.0     # Угол обзора (поле зрения)
        self.near = 0.1     # Ближняя плоскость отсечения
        self.far = 100.0    # Дальняя плоскость отсечения
        
        # СМЕЩЕНИЕ КАМЕРЫ (для панорамирования)
        self.pan_offset = [0.0, 0.0]
        
    def get_view_matrix(self):
        """Получение матрицы вида (как камера смотрит на сцену)"""
        # ВЫЧИСЛЕНИЕ НАПРАВЛЕНИЯ ВЗГЛЯДА ИЗ УГЛОВ ЭЙЛЕРА
        front = [
            math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch)),
            math.sin(math.radians(self.pitch)),
            math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        ]
        front = self.normalize(front)
        
        # ВЫЧИСЛЕНИЕ ВЕКТОРОВ "ВПРАВО" И "ВВЕРХ"
        right = self.normalize(self.cross(front, [0.0, 1.0, 0.0]))
        up = self.normalize(self.cross(right, front))
        
        # ПОЗИЦИЯ КАМЕРЫ С УЧЕТОМ СМЕЩЕНИЯ
        camera_pos = [
            self.position[0] + self.pan_offset[0],
            self.position[1] + self.pan_offset[1],
            self.position[2]
        ]
        
        # СОЗДАНИЕ LOOK-AT МАТРИЦЫ
        f = front
        r = right
        u = up
        p = camera_pos
        
        return np.array([
            [r[0], u[0], -f[0], 0.0],
            [r[1], u[1], -f[1], 0.0],
            [r[2], u[2], -f[2], 0.0],
            [-self.dot(r, p), -self.dot(u, p), self.dot(f, p), 1.0]
        ], dtype='f4')
    
    def get_projection_matrix(self):
        """Получение матрицы проекции (перспективная проекция)"""
        aspect = self.width / self.height  # Соотношение сторон
        f = 1.0 / math.tan(math.radians(self.fov) / 2.0)  # Фокусное расстояние
        
        return np.array([
            [f/aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (self.far+self.near)/(self.near-self.far), -1.0],
            [0.0, 0.0, (2*self.far*self.near)/(self.near-self.far), 0.0]
        ], dtype='f4')
    
    def rotate(self, dx, dy):
        """Вращение камеры"""
        self.yaw += dx * self.rotation_speed
        self.pitch -= dy * self.rotation_speed
        
        # ОГРАНИЧЕНИЕ ВЕРТИКАЛЬНОГО ПОВОРОТА (чтобы не перевернуться)
        self.pitch = max(-89.0, min(89.0, self.pitch))
    
    def pan(self, dx, dy):
        """Панорамирование (смещение) камеры"""
        self.pan_offset[0] += dx * 10
        self.pan_offset[1] -= dy * 10
    
    def zoom(self, amount):
        """Приближение/отдаление (изменение угла обзора)"""
        self.fov = max(10.0, min(120.0, self.fov - amount * self.zoom_speed))
    
    def reset(self):
        """Сброс камеры в начальное положение"""
        self.position = [0.0, 0.0, 20.0]
        self.yaw = -90.0
        self.pitch = 0.0
        self.fov = 60.0
        self.pan_offset = [0.0, 0.0]
    
    # ВСПОМОГАТЕЛЬНЫЕ МАТЕМАТИЧЕСКИЕ ФУНКЦИИ
    
    def normalize(self, v):
        """Нормализация вектора (приведение к длине 1)"""
        length = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if length > 0:
            return [v[0]/length, v[1]/length, v[2]/length]
        return v
    
    def cross(self, a, b):
        """Векторное произведение двух векторов"""
        return [
            a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]
        ]
    
    def dot(self, a, b):
        """Скалярное произведение двух векторов"""
        return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]