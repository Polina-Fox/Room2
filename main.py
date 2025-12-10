import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math

# Константы
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

class Camera:
    """Класс камеры для свободного перемещения внутри комнаты"""
    def __init__(self):
        # Позиция камеры ВНУТРИ комнаты
        self.position = np.array([0.0, 1.0, 2.0])  # Стартуем недалеко от входа
        
        # Направление взгляда (вектор вперед)
        self.front = np.array([0.0, 0.0, -1.0])  # Смотрим вглубь комнаты
        
        # Вектор "вверх" камеры
        self.up = np.array([0.0, 1.0, 0.0])
        
        # Углы Эйлера для вращения
        self.yaw = -90.0   # Поворот по горизонтали (0 = смотрим на +X)
        self.pitch = 0.0   # Наклон вверх/вниз
        
        # Чувствительность мыши
        self.mouse_sensitivity = 0.1
        
        # Скорость перемещения
        self.movement_speed = 0.1
        
        # Обновляем векторы камеры на основе углов
        self.update_camera_vectors()
        
        # Состояние клавиш для плавного управления
        self.keys_pressed = {
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_q: False,  # Вверх
            pygame.K_e: False   # Вниз
        }
    
    def update_camera_vectors(self):
        """Обновляет векторы камеры на основе углов Эйлера"""
        # Вычисляем новый вектор front
        front = np.array([
            math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch)),
            math.sin(math.radians(self.pitch)),
            math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        ])
        self.front = front / np.linalg.norm(front)  # Нормализуем
        
        # Вычисляем вектор right
        world_up = np.array([0.0, 1.0, 0.0])
        self.right = np.cross(self.front, world_up)
        self.right = self.right / np.linalg.norm(self.right)
        
        # Пересчитываем вектор up
        self.up = np.cross(self.right, self.front)
        self.up = self.up / np.linalg.norm(self.up)
    
    def process_mouse_movement(self, xoffset, yoffset):
        """Обрабатывает движение мыши"""
        self.yaw += xoffset * self.mouse_sensitivity
        self.pitch += yoffset * self.mouse_sensitivity
        
        # Ограничиваем угол pitch, чтобы не перевернуть камеру
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0
        
        # Обновляем векторы камеры
        self.update_camera_vectors()
    
    def process_keyboard(self):
        """Обрабатывает нажатия клавиш для движения"""
        velocity = self.movement_speed
        
        if self.keys_pressed[pygame.K_w]:  # Вперед
            self.position += self.front * velocity
        if self.keys_pressed[pygame.K_s]:  # Назад
            self.position -= self.front * velocity
        if self.keys_pressed[pygame.K_a]:  # Влево
            self.position -= self.right * velocity
        if self.keys_pressed[pygame.K_d]:  # Вправо
            self.position += self.right * velocity
        if self.keys_pressed[pygame.K_q]:  # Вверх
            self.position += self.up * velocity
        if self.keys_pressed[pygame.K_e]:  # Вниз
            self.position -= self.up * velocity
            
        # Ограничиваем позицию камеры внутри комнаты (примерно)
        room_half = 2.3  # Половина размера комнаты минус небольшой запас
        self.position[0] = max(-room_half, min(room_half, self.position[0]))
        self.position[1] = max(-1.8, min(4.5, self.position[1]))  # Не выходим за пол и потолок
        self.position[2] = max(-room_half, min(room_half, self.position[2]))
    
    def get_view_matrix(self):
        """Возвращает матрицу вида для камеры"""
        target = self.position + self.front
        return gluLookAt(
            self.position[0], self.position[1], self.position[2],  # Позиция камеры
            target[0], target[1], target[2],                      # Точка, на которую смотрим
            self.up[0], self.up[1], self.up[2]                    # Вектор "вверх"
        )
    
    def set_key(self, key, state):
        """Устанавливает состояние клавиши"""
        if key in self.keys_pressed:
            self.keys_pressed[key] = state

class CornellBoxApp:
    def __init__(self):
        # Инициализация pygame
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 
                                DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Корнуэльская комната - Компьютерная графика (WSAD + мышь)")
        
        # Скрываем курсор мыши
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)  # Захватываем мышь
        
        # Настройка OpenGL
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Чёрный фон
        
        # Настройка проекции
        glMatrixMode(GL_PROJECTION)
        gluPerspective(60, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 100.0)
        
        # Инициализация камеры
        self.camera = Camera()
        
        # Флаги управления
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Цвета для разных стен (как в классической Корнуэльской комнате)
        self.wall_colors = {
            'left': [0.8, 0.2, 0.2, 1.0],    # Красная стена
            'right': [0.2, 0.8, 0.2, 1.0],   # Зелёная стена  
            'back': [0.8, 0.8, 0.8, 1.0],    # Белая задняя стена
            'floor': [0.8, 0.8, 0.8, 1.0],   # Серый пол
            'ceiling': [0.8, 0.8, 0.8, 1.0], # Серый потолок
            'front': [0.5, 0.5, 0.5, 1.0]    # Серая передняя стена
        }
        
        # Параметры зеркальной стены (изначально - задняя стена)
        self.mirror_wall = 'back'  # 'left', 'right', 'back', 'floor', 'ceiling'
        self.mirror_enabled = False
        
        # Параметры второго источника света
        self.light1_position = [0.5, 3.0, -2.0, 1.0]
        self.light1_move_speed = 0.2
        
        # Объекты в комнате
        self.objects = []
        
        # Создаем тестовые объекты (все объекты БЕЗ спецэффектов по умолчанию)
        self.create_test_objects()
        
        # Шрифт для текста (уменьшим для экономии места)
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 13)  # Уменьшили с 14
        self.small_font = pygame.font.SysFont('Arial', 11)  # Уменьшили с 12
        
        # Счетчик FPS
        self.frame_count = 0
        self.fps = 0
        self.last_time = pygame.time.get_ticks()
    
    def create_test_objects(self):
        """Создаем тестовые объекты в комнате (ВСЕ объекты без спецэффектов по умолчанию!)"""
        # 1. Жёлтый куб - ПРАВЫЙ ПЕРЕДНИЙ УГОЛ
        self.objects.append({
            'id': 0,
            'type': 'cube',
            'position': [1.2, -1.5, -1.0],
            'scale': [0.5, 0.5, 0.5],
            'color': [0.9, 0.9, 0.0, 1.0],
            'mirror': False,
            'transparent': False,
            'shininess': 50.0
        })
        
        # 2. Синяя сфера - ЛЕВЫЙ СРЕДНИЙ ПЛАН
        self.objects.append({
            'id': 1,
            'type': 'sphere',
            'position': [-1.2, -1.0, -1.5],
            'scale': [0.4, 0.4, 0.4],
            'color': [0.2, 0.4, 0.9, 1.0],
            'mirror': False,
            'transparent': False,
            'shininess': 100.0
        })
        
        # 3. Красный КУБ (НЕПРОЗРАЧНЫЙ по умолчанию!)
        self.objects.append({
            'id': 2,
            'type': 'cube',
            'position': [0.0, -1.2, -2.0],
            'scale': [0.5, 0.5, 0.5],
            'color': [0.9, 0.3, 0.3, 1.0],  # Альфа = 1.0 (непрозрачный)
            'mirror': False,
            'transparent': False,  # НЕ прозрачный по умолчанию
            'shininess': 30.0
        })
        
        # 4. Зелёная сфера (НЕЗЕРКАЛЬНАЯ по умолчанию!)
        self.objects.append({
            'id': 3,
            'type': 'sphere',
            'position': [0.8, -0.3, -2.2],
            'scale': [0.4, 0.4, 0.4],
            'color': [0.2, 1.0, 0.2, 1.0],
            'mirror': False,  # НЕ зеркальная по умолчанию
            'transparent': False,
            'shininess': 50.0
        })
        
        # 5. Фиолетовая сфера
        self.objects.append({
            'id': 4,
            'type': 'sphere',
            'position': [-1.0, -1.5, -0.8],
            'scale': [0.3, 0.3, 0.3],
            'color': [0.9, 0.2, 0.9, 1.0],
            'mirror': False,
            'transparent': False,
            'shininess': 75.0
        })
    
    def toggle_mirror(self, obj_index):
        """Включает/выключает зеркальность для объекта"""
        if 0 <= obj_index < len(self.objects):
            self.objects[obj_index]['mirror'] = not self.objects[obj_index]['mirror']
    
    def toggle_transparency(self, obj_index):
        """Включает/выключает прозрачность для объекта"""
        if 0 <= obj_index < len(self.objects):
            self.objects[obj_index]['transparent'] = not self.objects[obj_index]['transparent']
            if self.objects[obj_index]['transparent']:
                self.objects[obj_index]['color'][3] = 0.6
            else:
                self.objects[obj_index]['color'][3] = 1.0
    
    def toggle_mirror_wall(self):
        """Переключает зеркальную стену"""
        walls = ['back', 'left', 'right', 'floor', 'ceiling']
        current_index = walls.index(self.mirror_wall)
        self.mirror_wall = walls[(current_index + 1) % len(walls)]
    
    def toggle_mirror_enabled(self):
        """Включает/выключает зеркальную стену"""
        self.mirror_enabled = not self.mirror_enabled
    
    def move_light1(self, direction):
        """Перемещает второй источник света"""
        if direction == 'up':
            self.light1_position[1] += self.light1_move_speed
        elif direction == 'down':
            self.light1_position[1] -= self.light1_move_speed
        elif direction == 'left':
            self.light1_position[0] -= self.light1_move_speed
        elif direction == 'right':
            self.light1_position[0] += self.light1_move_speed
        elif direction == 'forward':
            self.light1_position[2] -= self.light1_move_speed
        elif direction == 'backward':
            self.light1_position[2] += self.light1_move_speed
        
        # Ограничиваем позицию внутри комнаты
        room_half = 2.0
        self.light1_position[0] = max(-room_half, min(room_half, self.light1_position[0]))
        self.light1_position[1] = max(0.5, min(4.0, self.light1_position[1]))
        self.light1_position[2] = max(-room_half, min(room_half, self.light1_position[2]))
    
    def create_wall(self, vertices, color, normal=None, wall_name=''):
        """Создаёт одну стену комнаты с возможностью зеркальности"""
        is_mirror_wall = (wall_name == self.mirror_wall and self.mirror_enabled)
        
        if normal:
            glNormal3fv(normal)
        
        if is_mirror_wall:
            # Для зеркальной стены - максимальный блеск
            glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.1, 0.1, 0.15, 0.9])
            glMaterialfv(GL_FRONT, GL_AMBIENT, [0.05, 0.05, 0.1, 1.0])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 0.95, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, 128.0)
            glColor4f(0.15, 0.15, 0.25, 0.8)
        else:
            # Обычная стена
            glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            glMaterialfv(GL_FRONT, GL_AMBIENT, [c * 0.2 for c in color[:3]] + [1.0])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, 10.0)
            glColor3fv(color[:3])
        
        glBegin(GL_QUADS)
        for vertex in vertices:
            glVertex3fv(vertex)
        glEnd()
    
    def draw_cube(self, obj):
        """Рисует куб с учетом его свойств"""
        pos = obj['position']
        scale = obj['scale']
        color = obj['color']
        
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glScalef(scale[0], scale[1], scale[2])
        
        # Настраиваем свойства материала
        if obj['mirror']:
            glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.1, 0.1, 0.1, color[3]])
            glMaterialfv(GL_FRONT, GL_AMBIENT, [0.1, 0.1, 0.1, color[3]])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 0.9, color[3]])
            glMaterialf(GL_FRONT, GL_SHININESS, min(obj['shininess'], 128.0))
            glColor4f(0.7, 0.7, 0.7, color[3])
        else:
            glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            glMaterialfv(GL_FRONT, GL_AMBIENT, [c * 0.3 for c in color[:3]] + [color[3]])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, color[3]])
            glMaterialf(GL_FRONT, GL_SHININESS, min(obj['shininess'], 128.0))
            glColor4fv(color)
        
        # Если объект прозрачный
        if obj['transparent']:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDepthMask(GL_FALSE)
        else:
            glDisable(GL_BLEND)
            glDepthMask(GL_TRUE)
        
        # Рисуем куб
        glBegin(GL_QUADS)
        # Передняя грань
        glNormal3f(0, 0, 1)
        glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1)
        glVertex3f(1, 1, 1); glVertex3f(-1, 1, 1)
        # Задняя грань
        glNormal3f(0, 0, -1)
        glVertex3f(-1, -1, -1); glVertex3f(-1, 1, -1)
        glVertex3f(1, 1, -1); glVertex3f(1, -1, -1)
        # Верхняя грань
        glNormal3f(0, 1, 0)
        glVertex3f(-1, 1, -1); glVertex3f(-1, 1, 1)
        glVertex3f(1, 1, 1); glVertex3f(1, 1, -1)
        # Нижняя грань
        glNormal3f(0, -1, 0)
        glVertex3f(-1, -1, -1); glVertex3f(1, -1, -1)
        glVertex3f(1, -1, 1); glVertex3f(-1, -1, 1)
        # Правая грань
        glNormal3f(1, 0, 0)
        glVertex3f(1, -1, -1); glVertex3f(1, 1, -1)
        glVertex3f(1, 1, 1); glVertex3f(1, -1, 1)
        # Левая грань
        glNormal3f(-1, 0, 0)
        glVertex3f(-1, -1, -1); glVertex3f(-1, -1, 1)
        glVertex3f(-1, 1, 1); glVertex3f(-1, 1, -1)
        glEnd()
        
        # Восстанавливаем настройки
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glPopMatrix()
    
    def draw_sphere(self, obj, slices=16, stacks=16):
        """Рисует сферу с учетом её свойств"""
        pos = obj['position']
        scale = obj['scale']
        color = obj['color']
        
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glScalef(scale[0], scale[1], scale[2])
        
        # Настраиваем свойства материала
        if obj['mirror']:
            glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.1, 0.1, 0.1, color[3]])
            glMaterialfv(GL_FRONT, GL_AMBIENT, [0.1, 0.1, 0.1, color[3]])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 0.9, color[3]])
            glMaterialf(GL_FRONT, GL_SHININESS, min(obj['shininess'], 128.0))
            glColor4f(0.7, 0.7, 0.7, color[3])
        else:
            glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            glMaterialfv(GL_FRONT, GL_AMBIENT, [c * 0.3 for c in color[:3]] + [color[3]])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, color[3]])
            glMaterialf(GL_FRONT, GL_SHININESS, min(obj['shininess'], 128.0))
            glColor4fv(color)
        
        # Если объект прозрачный
        if obj['transparent']:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDepthMask(GL_FALSE)
        else:
            glDisable(GL_BLEND)
            glDepthMask(GL_TRUE)
        
        # Рисуем сферу
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = math.sin(lat0)
            zr0 = math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = math.sin(lat1)
            zr1 = math.cos(lat1)
            
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glNormal3f(x * zr0, y * zr0, z0)
                glVertex3f(x * zr0, y * zr0, z0)
                
                glNormal3f(x * zr1, y * zr1, z1)
                glVertex3f(x * zr1, y * zr1, z1)
            glEnd()
        
        # Восстанавливаем настройки
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glPopMatrix()
    
    def draw_cornell_box(self):
        """Рисуем корнуэльскую комнату изнутри"""
        room_size = 5.0
        
        # ВКЛЮЧАЕМ ОСВЕЩЕНИЕ
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        
        # Настраиваем модель освещения
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
        
        # Первый источник света (основной)
        light0_position = [0.0, 4.5, 0.0, 1.0]
        light0_diffuse = [1.0, 1.0, 1.0, 1.0]
        light0_ambient = [0.3, 0.3, 0.3, 1.0]
        light0_specular = [1.0, 1.0, 1.0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light0_position)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light0_specular)
        
        # Второй источник света
        light1_diffuse = [0.6, 0.8, 0.6, 1.0]
        light1_ambient = [0.1, 0.1, 0.1, 1.0]
        light1_specular = [0.5, 0.6, 0.5, 1.0]
        
        glLightfv(GL_LIGHT1, GL_POSITION, self.light1_position)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diffuse)
        glLightfv(GL_LIGHT1, GL_AMBIENT, light1_ambient)
        glLightfv(GL_LIGHT1, GL_SPECULAR, light1_specular)
        
        # Включаем нормализацию
        glEnable(GL_NORMALIZE)
        
        # Вершины комнаты
        half_size = room_size / 2.0
        
        # Задняя стена
        back_wall = [
            [-half_size, -half_size, -half_size],
            [half_size, -half_size, -half_size],
            [half_size, half_size, -half_size],
            [-half_size, half_size, -half_size]
        ]
        
        # Пол
        floor = [
            [-half_size, -half_size, half_size],
            [half_size, -half_size, half_size],
            [half_size, -half_size, -half_size],
            [-half_size, -half_size, -half_size]
        ]
        
        # Потолок
        ceiling = [
            [-half_size, half_size, -half_size],
            [half_size, half_size, -half_size],
            [half_size, half_size, half_size],
            [-half_size, half_size, half_size]
        ]
        
        # Левая стена (красная)
        left_wall = [
            [-half_size, -half_size, half_size],
            [-half_size, -half_size, -half_size],
            [-half_size, half_size, -half_size],
            [-half_size, half_size, half_size]
        ]
        
        # Правая стена (зелёная)
        right_wall = [
            [half_size, -half_size, -half_size],
            [half_size, -half_size, half_size],
            [half_size, half_size, half_size],
            [half_size, half_size, -half_size]
        ]
        
        # ПЕРЕДНЯЯ СТЕНА (ПОЛНАЯ)
        front_wall = [
            [-half_size, -half_size, half_size],
            [half_size, -half_size, half_size],
            [half_size, half_size, half_size],
            [-half_size, half_size, half_size]
        ]
        
        # Рисуем стены
        glPushMatrix()
        
        self.create_wall(back_wall, self.wall_colors['back'], 
                        normal=[0, 0, 1], wall_name='back')
        self.create_wall(floor, self.wall_colors['floor'], 
                        normal=[0, 1, 0], wall_name='floor')
        self.create_wall(ceiling, self.wall_colors['ceiling'], 
                        normal=[0, -1, 0], wall_name='ceiling')
        self.create_wall(left_wall, self.wall_colors['left'], 
                        normal=[1, 0, 0], wall_name='left')
        self.create_wall(right_wall, self.wall_colors['right'], 
                        normal=[-1, 0, 0], wall_name='right')
        self.create_wall(front_wall, self.wall_colors['front'], 
                        normal=[0, 0, -1], wall_name='front')
        
        glPopMatrix()
        
        # Рисуем объекты
        for obj in self.objects:
            if not obj['transparent']:
                if obj['type'] == 'cube':
                    self.draw_cube(obj)
                elif obj['type'] == 'sphere':
                    self.draw_sphere(obj)
        
        for obj in self.objects:
            if obj['transparent']:
                if obj['type'] == 'cube':
                    self.draw_cube(obj)
                elif obj['type'] == 'sphere':
                    self.draw_sphere(obj)
        
        # Источники света (точки)
        glDisable(GL_LIGHTING)
        
        # Первый источник света
        glPushMatrix()
        glTranslatef(light0_position[0], light0_position[1], light0_position[2])
        glColor3f(1.0, 1.0, 0.0)
        glPointSize(12.0)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        glPopMatrix()
        
        # Второй источник света
        glPushMatrix()
        glTranslatef(self.light1_position[0], self.light1_position[1], self.light1_position[2])
        glColor3f(0.6, 1.0, 0.6)
        glPointSize(10.0)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        glPopMatrix()
        
        glEnable(GL_LIGHTING)
    
    def draw_info_panel(self):
        """Рисует информационную панель с ОГРОМНЫМ размером"""
        current_time = pygame.time.get_ticks()
        self.frame_count += 1
        
        if current_time - self.last_time > 1000:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # ОГРОМНАЯ ПАНЕЛЬ - 500x600 пикселей
        panel_width = 500
        panel_height = 600
        
        # Создаем поверхность для текста
        info_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        info_surface.fill((0, 0, 0, 200))
        
        y_offset = 10
        
        # 1. ЗАГОЛОВОК
        title_text = self.font.render("=== КОРНУЭЛЬСКАЯ КОМНАТА ===", True, (255, 255, 150))
        info_surface.blit(title_text, (10, y_offset))
        y_offset += 25
        
        # FPS и позиция камеры
        fps_text = self.font.render(f"FPS: {self.fps}", True, (180, 255, 180))
        info_surface.blit(fps_text, (10, y_offset))
        y_offset += 20
        
        cam_text = self.small_font.render(f"Камера: X={self.camera.position[0]:.1f} Y={self.camera.position[1]:.1f} Z={self.camera.position[2]:.1f}", 
                                         True, (180, 180, 255))
        info_surface.blit(cam_text, (10, y_offset))
        y_offset += 25
        
        # 2. УПРАВЛЕНИЕ КАМЕРОЙ
        cam_title = self.font.render("=== УПРАВЛЕНИЕ КАМЕРОЙ ===", True, (255, 255, 200))
        info_surface.blit(cam_title, (10, y_offset))
        y_offset += 25
        
        cam_controls = [
            "WSAD - движение вперед/назад/влево/вправо",
            "Q/E - движение вверх/вниз",
            "Мышь - вращение камеры",
            "ESC - выход из программы"
        ]
        
        for line in cam_controls:
            text = self.small_font.render(line, True, (220, 220, 220))
            info_surface.blit(text, (15, y_offset))
            y_offset += 18
        
        y_offset += 10
        
        # 3. ОБЪЕКТЫ В КОМНАТЕ (компактнее)
        objects_title = self.font.render("=== ОБЪЕКТЫ В КОМНАТЕ ===", True, (255, 255, 200))
        info_surface.blit(objects_title, (10, y_offset))
        y_offset += 25
        
        # Компактный список объектов в 2 колонки
        for i, obj in enumerate(self.objects):
            obj_type = "К" if obj['type'] == 'cube' else "С"
            color_names = ["Ж", "Син", "Кр", "Зел", "Фил"]
            color_name = color_names[i] if i < len(color_names) else f"{i+1}"
            
            mirror_char = "✓" if obj['mirror'] else "·"
            trans_char = "✓" if obj['transparent'] else "·"
            
            # Цвет текста в зависимости от состояния
            if obj['mirror']:
                text_color = (100, 255, 100)  # Зелёный для зеркала
            elif obj['transparent']:
                text_color = (100, 200, 255)  # Голубой для прозрачности
            else:
                text_color = (200, 200, 200)  # Серый без эффектов
            
            # Компактный формат: "1.КЖ:М[✓]П[·]"
            status_line = f"{i+1}.{obj_type}{color_name}:М[{mirror_char}]П[{trans_char}]"
            
            # Распределяем в 2 колонки
            col = i % 2
            row = i // 2
            x_pos = 15 + (col * 240)
            y_pos = y_offset + (row * 18)
            
            text = self.small_font.render(status_line, True, text_color)
            info_surface.blit(text, (x_pos, y_pos))
        
        # Пересчитываем y_offset после объектов
        rows_needed = (len(self.objects) + 1) // 2  # +1 для округления вверх
        y_offset += rows_needed * 18 + 10
        
        # 4. УПРАВЛЕНИЕ ОБЪЕКТАМИ
        obj_controls_title = self.font.render("=== УПРАВЛЕНИЕ ОБЪЕКТАМИ ===", True, (255, 255, 200))
        info_surface.blit(obj_controls_title, (10, y_offset))
        y_offset += 25
        
        obj_controls = [
            "Клавиши 1-5: ЗЕРКАЛЬНОСТЬ объектов (1=жёлтый, 2=синий...)",
            "Клавиши 6-0: ПРОЗРАЧНОСТЬ объектов (6=жёлтый, 7=синий...)",
            "R: сбросить все настройки"
        ]
        
        for line in obj_controls:
            text = self.small_font.render(line, True, (220, 220, 220))
            info_surface.blit(text, (15, y_offset))
            y_offset += 18
        
        y_offset += 10
        
        # 5. ЗЕРКАЛЬНАЯ СТЕНА - ТЕПЕРЬ ВИДНО!
        mirror_title = self.font.render("=== ЗЕРКАЛЬНАЯ СТЕНА ===", True, (255, 255, 200))
        info_surface.blit(mirror_title, (10, y_offset))
        y_offset += 25
        
        # Статус зеркальной стены
        wall_status = "ВКЛЮЧЕНА" if self.mirror_enabled else "ВЫКЛЮЧЕНА"
        status_color = (100, 255, 100) if self.mirror_enabled else (255, 100, 100)
        
        wall_info = [
            f"Текущая стена: {self.mirror_wall}",
            f"Состояние: {wall_status}",
            "M: сменить зеркальную стену",
            "N: включить/выключить зеркало"
        ]
        
        for j, line in enumerate(wall_info):
            if j == 1:  # Строка со статусом
                text_color = status_color
            else:
                text_color = (220, 220, 220)
            
            text = self.small_font.render(line, True, text_color)
            info_surface.blit(text, (15, y_offset))
            y_offset += 18
        
        y_offset += 10
        
        # 6. УПРАВЛЕНИЕ ВТОРЫМ ИСТОЧНИКОМ СВЕТА - ТЕПЕРЬ ТОЧНО ВИДНО!
        light_title = self.font.render("=== УПРАВЛЕНИЕ ВТОРЫМ СВЕТОМ ===", True, (255, 255, 200))
        info_surface.blit(light_title, (10, y_offset))
        y_offset += 25
        
        # Позиция света (очень важно!)
        light_pos = f"ПОЗИЦИЯ СВЕТА: X={self.light1_position[0]:.1f} Y={self.light1_position[1]:.1f} Z={self.light1_position[2]:.1f}"
        pos_text = self.font.render(light_pos, True, (180, 255, 180))
        info_surface.blit(pos_text, (15, y_offset))
        y_offset += 25
        
        # Управление светом - ВЫДЕЛЯЕМ КЛАВИШИ
        light_controls = [
            "U / J  -  двигать свет ВВЕРХ / ВНИЗ",
            "H / K  -  двигать свет ВЛЕВО / ВПРАВО", 
            "Y / I  -  двигать свет БЛИЖЕ / ДАЛЬШЕ"
        ]
        
        for line in light_controls:
            text = self.font.render(line, True, (180, 200, 255))
            info_surface.blit(text, (20, y_offset))
            y_offset += 25
        
        # ОТОБРАЖЕНИЕ ПАНЕЛИ
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        # Сохраняем текущие матрицы
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Включаем смешивание для прозрачности
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Рисуем фон панели
        glColor4f(0.0, 0.0, 0.0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(5, SCREEN_HEIGHT - 5 - panel_height)
        glVertex2f(5 + panel_width, SCREEN_HEIGHT - 5 - panel_height)
        glVertex2f(5 + panel_width, SCREEN_HEIGHT - 5)
        glVertex2f(5, SCREEN_HEIGHT - 5)
        glEnd()
        
        # Преобразуем поверхность Pygame в текстуру OpenGL
        texture_data = pygame.image.tostring(info_surface, "RGBA", True)
        width, height = info_surface.get_size()
        
        # Создаем и настраиваем текстуру
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, 
                    GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Включаем текстурирование
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        
        # Рисуем текстуру
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(5, SCREEN_HEIGHT - 5 - height)
        glTexCoord2f(1.0, 0.0); glVertex2f(5 + width, SCREEN_HEIGHT - 5 - height)
        glTexCoord2f(1.0, 1.0); glVertex2f(5 + width, SCREEN_HEIGHT - 5)
        glTexCoord2f(0.0, 1.0); glVertex2f(5, SCREEN_HEIGHT - 5)
        glEnd()
        
        # Отключаем текстурирование
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        
        # Удаляем текстуру
        glDeleteTextures([tex_id])
        
        # Восстанавливаем матрицы
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Восстанавливаем настройки
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in self.camera.keys_pressed:
                    self.camera.set_key(event.key, True)
                
                # Управление свойствами объектов
                elif event.key == pygame.K_1:
                    self.toggle_mirror(0)
                elif event.key == pygame.K_2:
                    self.toggle_mirror(1)
                elif event.key == pygame.K_3:
                    self.toggle_mirror(2)
                elif event.key == pygame.K_4:
                    self.toggle_mirror(3)
                elif event.key == pygame.K_5:
                    self.toggle_mirror(4)
                
                elif event.key == pygame.K_6:
                    self.toggle_transparency(0)
                elif event.key == pygame.K_7:
                    self.toggle_transparency(1)
                elif event.key == pygame.K_8:
                    self.toggle_transparency(2)
                elif event.key == pygame.K_9:
                    self.toggle_transparency(3)
                elif event.key == pygame.K_0:
                    self.toggle_transparency(4)
                
                # Управление зеркальной стеной
                elif event.key == pygame.K_m:
                    self.toggle_mirror_wall()
                elif event.key == pygame.K_n:
                    self.toggle_mirror_enabled()
                
                # Управление вторым источником света
                elif event.key == pygame.K_u:
                    self.move_light1('up')
                elif event.key == pygame.K_j:
                    self.move_light1('down')
                elif event.key == pygame.K_h:
                    self.move_light1('left')
                elif event.key == pygame.K_k:
                    self.move_light1('right')
                elif event.key == pygame.K_y:
                    self.move_light1('forward')
                elif event.key == pygame.K_i:
                    self.move_light1('backward')
                
                # Сброс настроек
                elif event.key == pygame.K_r:
                    self.reset_settings()
            
            elif event.type == pygame.KEYUP:
                if event.key in self.camera.keys_pressed:
                    self.camera.set_key(event.key, False)
            
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                
                if x != center_x or y != center_y:
                    dx, dy = x - center_x, y - center_y
                    self.camera.process_mouse_movement(dx, -dy)
                    pygame.mouse.set_pos((center_x, center_y))
    
    def reset_settings(self):
        """Сбрасывает все настройки к начальным"""
        for obj in self.objects:
            obj['mirror'] = False
            obj['transparent'] = False
            obj['color'][3] = 1.0
        
        self.mirror_wall = 'back'
        self.mirror_enabled = False
        self.light1_position = [0.5, 3.0, -2.0, 1.0]
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # ИСПРАВЛЕНО: было Бит, стало BIT
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.get_view_matrix()
        
        # Обработка клавиш для движения камеры
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.camera.position += self.camera.front * self.camera.movement_speed
        if keys[pygame.K_s]:
            self.camera.position -= self.camera.front * self.camera.movement_speed
        if keys[pygame.K_a]:
            self.camera.position -= self.camera.right * self.camera.movement_speed
        if keys[pygame.K_d]:
            self.camera.position += self.camera.right * self.camera.movement_speed
        if keys[pygame.K_q]:
            self.camera.position += self.camera.up * self.camera.movement_speed
        if keys[pygame.K_e]:
            self.camera.position -= self.camera.up * self.camera.movement_speed
        
        self.draw_cornell_box()
        self.draw_info_panel()
        
        pygame.display.flip()
    
    def run(self):
        pygame.mouse.set_pos((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    app = CornellBoxApp()
    app.run()