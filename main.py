# -*- coding: utf-8 -*-
"""
Cornell Box - Проект по компьютерной графике
Реализация Корнуэльской комнаты с интерактивным управлением
"""

import pygame
import moderngl
import numpy as np
import sys
import os
from objects import Cube, Sphere
from materials import Material
from camera import Camera
from ui import UI

class CornellBox:
    def __init__(self, width=1200, height=800):
        """Инициализация приложения"""
        # Инициализация PyGame
        pygame.init()
        
        # Настройка OpenGL контекста
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        
        # Настройка окна
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        
        # Настройка OpenGL
        self.ctx.enable(moderngl.DEPTH_TEST)  # Включить тест глубины
        self.ctx.enable(moderngl.BLEND)       # Включить прозрачность
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Инициализация списков перед загрузкой шейдеров
        self.objects = {}  # Словарь для хранения объектов
        self.render_objects = []  # Список всех объектов для рендеринга
        self.object_states = {}  # Словарь состояний объектов
        self.lights = []  # Список источников света
        
        # Загрузка шейдеров
        self.load_shaders()
        
        # Создание камеры
        self.camera = Camera(width, height)
        
        # Создание интерфейса
        self.ui = UI(width, height)
        
        # Время для анимации
        self.time = 0.0
        
        # Флаги управления
        self.running = True     # Флаг работы приложения
        self.show_ui = True     # Показывать ли интерфейс
        
        # Цвет фона (окружения)
        self.environment_color = [0.2, 0.2, 0.3]  # Темно-синий
        
        # Индекс текущего перемещаемого света
        self.moving_light_index = 1  # Второй свет по умолчанию
        
        # Зеркальная стена (по умолчанию нет)
        self.mirror_wall = None
        
        # Создание сцены
        self.create_scene()
        
        # Создание источников света
        self.create_lights()
        
    def load_shaders(self):
        """Загрузка шейдеров (встроенные шейдеры)"""
        # Вершинный шейдер
        vertex_source = """
        #version 330
        in vec3 in_position;
        in vec3 in_normal;
        out vec3 v_position;
        out vec3 v_normal;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        void main() {
            vec4 world_pos = model * vec4(in_position, 1.0);
            v_position = world_pos.xyz;
            v_normal = mat3(transpose(inverse(model))) * in_normal;
            gl_Position = projection * view * world_pos;
        }
        """
        
        # Фрагментный шейдер - ИСПРАВЛЕННАЯ ВЕРСИЯ
        fragment_source = """
        #version 330
        in vec3 v_position;
        in vec3 v_normal;
        out vec4 frag_color;
        
        uniform vec3 material_diffuse;
        uniform vec3 material_specular;
        uniform float material_shininess;
        uniform float material_alpha;
        uniform vec3 material_emission;
        
        uniform vec3 light_positions[4];
        uniform vec3 light_colors[4];
        uniform float light_intensities[4];
        uniform int num_lights;
        uniform vec3 view_pos;
        
        void main() {
            vec3 normal = normalize(v_normal);
            vec3 view_dir = normalize(view_pos - v_position);
            vec3 result = material_emission;
            
            // Проверяем количество активных источников света
            int lights_to_process = min(num_lights, 4);
            
            for (int i = 0; i < lights_to_process; i++) {
                vec3 light_dir = normalize(light_positions[i] - v_position);
                float diff = max(dot(normal, light_dir), 0.0);
                vec3 diffuse = light_colors[i] * diff * material_diffuse * light_intensities[i];
                
                // Простой расчет бликов
                if (material_shininess > 0.0) {
                    vec3 reflect_dir = reflect(-light_dir, normal);
                    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), material_shininess);
                    vec3 specular = light_colors[i] * spec * material_specular * light_intensities[i];
                    result += specular;
                }
                
                result += diffuse;
            }
            
            vec3 ambient = vec3(0.1) * material_diffuse;
            result += ambient;
            
            frag_color = vec4(result, material_alpha);
        }
        """
        
        self.program = self.ctx.program(
            vertex_shader=vertex_source,
            fragment_shader=fragment_source
        )
        
    def create_scene(self):
        """Создание всей сцены Корнуэльской комнаты"""
        room_size = 15.0    # Размер комнаты
        wall_thickness = 0.2  # Толщина стен
        
        # 1. СОЗДАНИЕ КОМНАТЫ (6 стен)
        # Материалы для стен
        room_materials = {
            'left': Material(diffuse=[0.9, 0.1, 0.1], name="Левая стена (красная)"),
            'right': Material(diffuse=[0.1, 0.9, 0.1], name="Правая стена (зеленая)"),
            'back': Material(diffuse=[0.9, 0.9, 0.9], name="Задняя стена (серая)"),
            'floor': Material(diffuse=[0.8, 0.8, 0.8], name="Пол (серый)"),
            'ceiling': Material(diffuse=[0.9, 0.9, 0.9], name="Потолок (белый)"),
            'front': Material(diffuse=[0.0, 0.0, 0.0], name="Передняя стена (черная)"),  # Не видна
        }
        
        # Конфигурация стен: позиция и размер
        walls_config = {
            'left': {
                'pos': [-room_size/2 - wall_thickness/2, 0, -room_size/3], 
                'size': [wall_thickness, room_size, room_size*2/3]
            },
            'right': {
                'pos': [room_size/2 + wall_thickness/2, 0, -room_size/3], 
                'size': [wall_thickness, room_size, room_size*2/3]
            },
            'back': {
                'pos': [0, 0, -room_size*2/3 - wall_thickness/2], 
                'size': [room_size, room_size, wall_thickness]
            },
            'floor': {
                'pos': [0, -room_size/2 - wall_thickness/2, -room_size/3], 
                'size': [room_size, wall_thickness, room_size*2/3]
            },
            'ceiling': {
                'pos': [0, room_size/2 + wall_thickness/2, -room_size/3], 
                'size': [room_size, wall_thickness, room_size*2/3]
            },
            'front': {
                'pos': [0, 0, room_size/3 + wall_thickness/2], 
                'size': [room_size, room_size, wall_thickness]
            },
        }
        
        # Создание стен
        for wall_name, config in walls_config.items():
            wall = Cube(
                ctx=self.ctx,
                program=self.program,
                position=config['pos'],
                size=config['size'],
                material=room_materials[wall_name]
            )
            self.objects[f'wall_{wall_name}'] = wall
            self.render_objects.append(wall)
        
        # 2. СОЗДАНИЕ ОСНОВНЫХ ОБЪЕКТОВ
        
        # ОБЪЕКТ 1: Большой куб (желтый, непрозрачный, неотражающий)
        cube1_mat = Material(
            diffuse=[1.0, 1.0, 0.0],  # Желтый цвет
            specular=[0.0, 0.0, 0.0],  # Нет зеркальности
            shininess=0.0,             # Без бликов
            alpha=1.0,                 # Полностью непрозрачный
            name="Большой куб"
        )
        self.objects['cube1'] = Cube(
            self.ctx, self.program, 
            position=[-5.0, -4.0, -8.0],  # Позиция в комнате
            size=3.0,                     # Размер
            material=cube1_mat
        )
        self.render_objects.append(self.objects['cube1'])
        # Состояние объекта: зеркальность и прозрачность
        self.object_states['cube1'] = {'mirror': False, 'transparent': False}
        
        # ОБЪЕКТ 2: Второй куб (голубой) - +1 балл
        cube2_mat = Material(
            diffuse=[0.0, 0.7, 1.0],  # Голубой цвет
            specular=[0.0, 0.0, 0.0],
            shininess=0.0,
            alpha=1.0,
            name="Голубой куб"
        )
        self.objects['cube2'] = Cube(
            self.ctx, self.program,
            position=[5.0, -4.0, -8.0],
            size=2.5,
            material=cube2_mat
        )
        self.render_objects.append(self.objects['cube2'])
        self.object_states['cube2'] = {'mirror': False, 'transparent': False}
        
        # ОБЪЕКТ 3: Сфера (пурпурная) - +1 балл (первый объект другого вида)
        sphere1_mat = Material(
            diffuse=[1.0, 0.0, 1.0],  # Пурпурный цвет
            specular=[0.0, 0.0, 0.0],
            shininess=0.0,
            alpha=1.0,
            name="Пурпурная сфера"
        )
        self.objects['sphere1'] = Sphere(
            self.ctx, self.program,
            position=[0.0, 3.0, -10.0],
            radius=2.0,               # Радиус сферы
            material=sphere1_mat,
            segments=32               # Количество сегментов (качество)
        )
        self.render_objects.append(self.objects['sphere1'])
        self.object_states['sphere1'] = {'mirror': False, 'transparent': False}
        
        # ОБЪЕКТ 4: Маленькая сфера (оранжевая) - +1 балл (второй объект другого вида)
        sphere2_mat = Material(
            diffuse=[1.0, 0.5, 0.0],  # Оранжевый цвет
            specular=[0.0, 0.0, 0.0],
            shininess=0.0,
            alpha=1.0,
            name="Оранжевая сфера"
        )
        self.objects['sphere2'] = Sphere(
            self.ctx, self.program,
            position=[-2.0, -2.0, -5.0],
            radius=1.5,
            material=sphere2_mat,
            segments=24
        )
        self.render_objects.append(self.objects['sphere2'])
        self.object_states['sphere2'] = {'mirror': False, 'transparent': False}
        
    def create_lights(self):
        """Создание источников света"""
        # ИСТОЧНИК 1: Основной источник (точечный свет)
        light1_mat = Material(
            diffuse=[1.0, 1.0, 1.0],
            specular=[1.0, 1.0, 1.0],
            emission=[1.0, 1.0, 0.9],  # Слегка теплый свет
            shininess=1.0,
            alpha=1.0
        )
        
        # Визуальное представление источника света (сфера)
        self.light1_obj = Sphere(
            self.ctx, self.program,
            position=[0.0, 12.0, -5.0],  # Позиция вверху комнаты
            radius=0.5,                   # Размер сферы
            material=light1_mat,
            segments=16
        )
        self.render_objects.append(self.light1_obj)
        
        # Данные для шейдера
        self.lights.append({
            'position': [0.0, 12.0, -5.0],
            'color': [1.0, 1.0, 0.9],
            'intensity': 1.2,
            'enabled': True,
            'name': 'Основной свет'
        })
        
        # ИСТОЧНИК 2: Дополнительный источник - +1 балл
        light2_mat = Material(
            diffuse=[1.0, 1.0, 1.0],
            specular=[1.0, 1.0, 1.0],
            emission=[0.8, 0.9, 1.0],  # Слегка холодный свет
            shininess=1.0,
            alpha=1.0
        )
        
        self.light2_obj = Sphere(
            self.ctx, self.program,
            position=[-8.0, 5.0, -3.0],
            radius=0.4,
            material=light2_mat,
            segments=16
        )
        self.render_objects.append(self.light2_obj)
        
        self.lights.append({
            'position': [-8.0, 5.0, -3.0],
            'color': [0.8, 0.9, 1.0],
            'intensity': 0.8,
            'enabled': True,
            'name': 'Дополнительный свет',
            'movable': True  # Можно перемещать
        })
        
    def update_materials(self):
        """Обновление всех материалов на основе текущих состояний"""
        # ОБНОВЛЕНИЕ ОБЪЕКТОВ
        for obj_name, state in self.object_states.items():
            if obj_name in self.objects:
                obj = self.objects[obj_name]
                
                # Включение/выключение зеркальности
                if state['mirror']:
                    obj.material.specular = [0.8, 0.8, 0.8]  # Зеркальный цвет
                    obj.material.shininess = 120.0           # Сила бликов
                else:
                    obj.material.specular = [0.0, 0.0, 0.0]  # Нет зеркальности
                    obj.material.shininess = 0.0
                
                # Включение/выключение прозрачности
                if state['transparent']:
                    obj.material.alpha = 0.4  # Полупрозрачный
                else:
                    obj.material.alpha = 1.0  # Непрозрачный
        
        # ОБНОВЛЕНИЕ СТЕН (зеркальная стена)
        for wall_key in ['wall_left', 'wall_right', 'wall_back', 'wall_floor', 'wall_ceiling']:
            if wall_key in self.objects:
                wall = self.objects[wall_key]
                wall_name = wall_key.replace('wall_', '')
                
                if self.mirror_wall == wall_name:
                    # Делаем стену зеркальной
                    wall.material.specular = [0.9, 0.9, 0.9]
                    wall.material.shininess = 200.0
                else:
                    # Возвращаем обычный материал
                    wall.material.specular = [0.0, 0.0, 0.0]
                    wall.material.shininess = 0.0
        
        # ОБНОВЛЕНИЕ ИСТОЧНИКОВ СВЕТА
        for i, light in enumerate(self.lights):
            if i == 0:  # Первый свет
                self.light1_obj.position = light['position']
            elif i == 1:  # Второй свет
                self.light2_obj.position = light['position']
    
    def handle_events(self):
        """Обработка всех событий приложения"""
        for event in pygame.event.get():
            # ВЫХОД ИЗ ПРИЛОЖЕНИЯ
            if event.type == pygame.QUIT:
                self.running = False
            
            # ОБРАБОТКА ИНТЕРФЕЙСА
            if self.show_ui:
                ui_result = self.ui.handle_event(event)
                if ui_result:
                    self.handle_ui_action(ui_result)
            
            # УПРАВЛЕНИЕ КАМЕРОЙ МЫШЬЮ
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # Левая кнопка мыши
                    dx, dy = event.rel  # Относительное движение
                    self.camera.rotate(dx * 0.5, dy * 0.5)
                elif pygame.mouse.get_pressed()[2]:  # Правая кнопка мыши
                    dx, dy = event.rel
                    self.camera.pan(dx * 0.01, dy * 0.01)
            
            # ПРОКРУТКА КОЛЕСИКА МЫШИ
            if event.type == pygame.MOUSEWHEEL:
                self.camera.zoom(event.y * 2.0)  # event.y = направление прокрутки
            
            # НАЖАТИЯ КЛАВИШ
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
    
    def handle_keydown(self, event):
        """Обработка нажатий клавиш"""
        # БЫСТРЫЕ КЛАВИШИ ДЛЯ ОТЛАДКИ
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_u:
            self.show_ui = not self.show_ui  # Показать/скрыть UI
        elif event.key == pygame.K_r:
            self.camera.reset()  # Сброс камеры
        
        # УПРАВЛЕНИЕ ПЕРЕМЕЩАЕМЫМ ИСТОЧНИКОМ СВЕТА
        if self.lights and self.moving_light_index < len(self.lights):
            light = self.lights[self.moving_light_index]
            speed = 0.5  # Скорость перемещения
            
            if event.key == pygame.K_w:
                light['position'][2] -= speed  # Вперед
            elif event.key == pygame.K_s:
                light['position'][2] += speed  # Назад
            elif event.key == pygame.K_a:
                light['position'][0] -= speed  # Влево
            elif event.key == pygame.K_d:
                light['position'][0] += speed  # Вправо
            elif event.key == pygame.K_q:
                light['position'][1] += speed  # Вверх
            elif event.key == pygame.K_e:
                light['position'][1] -= speed  # Вниз
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                light['intensity'] = min(2.0, light['intensity'] + 0.1)  # Увеличить интенсивность
            elif event.key == pygame.K_MINUS:
                light['intensity'] = max(0.1, light['intensity'] - 0.1)  # Уменьшить интенсивность
        
        # ПЕРЕКЛЮЧЕНИЕ МЕЖДУ ИСТОЧНИКАМИ СВЕТА
        if event.key == pygame.K_TAB and self.lights:
            self.moving_light_index = (self.moving_light_index + 1) % len(self.lights)
    
    def handle_ui_action(self, action):
        """Обработка действий из интерфейса"""
        if action.startswith('toggle_mirror_'):
            # Включить/выключить зеркальность объекта
            obj_name = action.replace('toggle_mirror_', '')
            if obj_name in self.object_states:
                self.object_states[obj_name]['mirror'] = not self.object_states[obj_name]['mirror']
        
        elif action.startswith('toggle_transparent_'):
            # Включить/выключить прозрачность объекта
            obj_name = action.replace('toggle_transparent_', '')
            if obj_name in self.object_states:
                self.object_states[obj_name]['transparent'] = not self.object_states[obj_name]['transparent']
        
        elif action.startswith('mirror_wall_'):
            # Выбор зеркальной стены
            wall_name = action.replace('mirror_wall_', '')
            if wall_name == 'none':
                self.mirror_wall = None
            else:
                self.mirror_wall = wall_name
        
        elif action == 'toggle_light1' and len(self.lights) > 0:
            # Включить/выключить первый свет
            self.lights[0]['enabled'] = not self.lights[0]['enabled']
        
        elif action == 'toggle_light2' and len(self.lights) > 1:
            # Включить/выключить второй свет
            self.lights[1]['enabled'] = not self.lights[1]['enabled']
        
        elif action == 'switch_moving_light' and self.lights:
            # Переключить перемещаемый свет
            self.moving_light_index = (self.moving_light_index + 1) % len(self.lights)
        
        elif action == 'reset_camera':
            # Сброс камеры
            self.camera.reset()
        
        elif action == 'toggle_ui':
            # Показать/скрыть интерфейс
            self.show_ui = not self.show_ui
    
    def update(self, dt):
        """Обновление состояния сцены"""
        self.time += dt  # Увеличиваем время
        
        # ЛЕГКАЯ АНИМАЦИЯ ОБЪЕКТОВ (вращение)
        rotation_speed = 0.3
        if 'cube1' in self.objects:
            self.objects['cube1'].rotation[1] = self.time * rotation_speed  # Вращение по Y
        
        if 'sphere1' in self.objects:
            self.objects['sphere1'].rotation[0] = self.time * rotation_speed * 0.7  # Вращение по X
            self.objects['sphere1'].rotation[1] = self.time * rotation_speed * 0.5  # Вращение по Y
        
        # Обновление материалов
        self.update_materials()
        
        # Обновление интерфейса
        self.ui.update(self.object_states, self.lights, self.moving_light_index, self.mirror_wall)
    
    def render(self):
        """Рендеринг всей сцены"""
        # ОЧИСТКА ЭКРАНА
        self.ctx.clear(*self.environment_color)
        
        # ПОЛУЧЕНИЕ МАТРИЦ КАМЕРЫ
        view_matrix = self.camera.get_view_matrix()
        projection_matrix = self.camera.get_projection_matrix()
        
        # УСТАНОВКА UNIFORM-ПЕРЕМЕННЫХ В ШЕЙДЕР
        self.program['view'].write(view_matrix.tobytes())
        self.program['projection'].write(projection_matrix.tobytes())
        self.program['view_pos'].write(np.array(self.camera.position, dtype='f4').tobytes())
        
        # ПОДГОТОВКА ДАННЫХ ОБ ИСТОЧНИКАХ СВЕТА
        enabled_lights = [light for light in self.lights if light['enabled']]
        num_lights = min(len(enabled_lights), 4)  # Максимум 4 источника света
        
        if num_lights > 0:
            # Подготавливаем массивы фиксированного размера (4 источника)
            light_positions = np.zeros((4, 3), dtype='f4')
            light_colors = np.zeros((4, 3), dtype='f4')
            light_intensities = np.zeros(4, dtype='f4')
            
            # Заполняем данные
            for i in range(num_lights):
                light_positions[i] = enabled_lights[i]['position']
                light_colors[i] = enabled_lights[i]['color']
                light_intensities[i] = enabled_lights[i]['intensity']
            
            # Передача данных в шейдер
            self.program['num_lights'].value = num_lights
            self.program['light_positions'].write(light_positions.tobytes())
            self.program['light_colors'].write(light_colors.tobytes())
            self.program['light_intensities'].write(light_intensities.tobytes())
        else:
            self.program['num_lights'].value = 0  # Нет активных источников света
        
        # РЕНДЕРИНГ ВСЕХ ОБЪЕКТОВ
        for obj in self.render_objects:
            obj.render(self.program)
        
        # РЕНДЕРИНГ ИНТЕРФЕЙСА (поверх 3D)
        if self.show_ui:
            self.ui.render(self.screen)
        
        # ОБНОВЛЕНИЕ ДИСПЛЕЯ
        pygame.display.flip()
    
    def run(self):
        """Главный цикл приложения"""
        clock = pygame.time.Clock()
        
        while self.running:
            dt = clock.tick(60) / 1000.0  # Дельта времени в секундах (60 FPS)
            
            # ОБРАБОТКА СОБЫТИЙ
            self.handle_events()
            
            # ОБНОВЛЕНИЕ СОСТОЯНИЯ
            self.update(dt)
            
            # РЕНДЕРИНГ
            self.render()
        
        # ЗАВЕРШЕНИЕ ПРИЛОЖЕНИЯ
        pygame.quit()
        sys.exit()

# ЗАПУСК ПРИЛОЖЕНИЯ
if __name__ == '__main__':
    app = CornellBox()
    app.run()