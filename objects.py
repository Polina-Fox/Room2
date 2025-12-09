"""
Классы для создания 3D-объектов (Куб, Сфера)
"""

import numpy as np
import moderngl
import math

class BaseObject:
    """Базовый класс для всех 3D-объектов"""
    def __init__(self, ctx, program, position, material):
        # OpenGL контекст
        self.ctx = ctx
        
        # Шейдерная программа
        self.program = program
        
        # Позиция объекта в мире [x, y, z]
        self.position = list(position)
        
        # Материал объекта
        self.material = material
        
        # Вращение объекта [x, y, z] в градусах
        self.rotation = [0.0, 0.0, 0.0]
        
        # Масштаб объекта [x, y, z]
        self.scale = [1.0, 1.0, 1.0]
        
    def get_model_matrix(self):
        """Создание матрицы модели (преобразования объекта)"""
        # ПЕРЕНОС (TRANSLATION)
        tx, ty, tz = self.position
        translation = np.array([
            [1.0, 0.0, 0.0, tx],
            [0.0, 1.0, 0.0, ty],
            [0.0, 0.0, 1.0, tz],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype='f4')
        
        # ВРАЩЕНИЕ (ROTATION) - только вокруг оси Y для простоты
        rx, ry, rz = self.rotation
        angle_y = math.radians(ry)  # Преобразование в радианы
        cos_y = math.cos(angle_y)
        sin_y = math.sin(angle_y)
        
        rotation_y = np.array([
            [cos_y, 0.0, sin_y, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-sin_y, 0.0, cos_y, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype='f4')
        
        # МАСШТАБИРОВАНИЕ (SCALING)
        sx, sy, sz = self.scale
        scaling = np.array([
            [sx, 0.0, 0.0, 0.0],
            [0.0, sy, 0.0, 0.0],
            [0.0, 0.0, sz, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype='f4')
        
        # КОМБИНИРОВАНИЕ: масштаб * вращение * перенос
        model = translation @ rotation_y @ scaling
        return model
    
    def set_material_uniforms(self, program):
        """Установка параметров материала в шейдер"""
        # Передача диффузного цвета
        program['material_diffuse'].write(np.array(self.material.diffuse, dtype='f4').tobytes())
        
        # Передача зеркального цвета
        program['material_specular'].write(np.array(self.material.specular, dtype='f4').tobytes())
        
        # Передача силы блеска
        program['material_shininess'].write(np.array([self.material.shininess], dtype='f4').tobytes())
        
        # Передача прозрачности
        program['material_alpha'].write(np.array([self.material.alpha], dtype='f4').tobytes())
        
        # Передача свечения
        program['material_emission'].write(np.array(self.material.emission, dtype='f4').tobytes())

class Cube(BaseObject):
    """Класс для создания куба"""
    def __init__(self, ctx, program, position, size, material):
        super().__init__(ctx, program, position, material)
        
        # Если размер задан одним числом, делаем куб равносторонним
        if isinstance(size, (int, float)):
            size = [size, size, size]
        
        self.size = size  # Размеры куба [ширина, высота, глубина]
        
        # Создание геометрии куба
        self.vertices, self.normals, self.indices = self.create_cube_geometry(size)
        
        # Создание OpenGL буферов
        self.create_buffers()
    
    def create_cube_geometry(self, size):
        """Создание вершин, нормалей и индексов для куба"""
        sx, sy, sz = size
        half_sx, half_sy, half_sz = sx/2, sy/2, sz/2
        
        # Вершины для 6 граней куба (по 4 вершины на грань)
        vertices = []
        normals = []
        indices = []
        
        # ПЕРЕДНЯЯ ГРАНЬ
        vertices.extend([
            [-half_sx, -half_sy,  half_sz],  # 0: Нижний левый
            [ half_sx, -half_sy,  half_sz],  # 1: Нижний правый
            [ half_sx,  half_sy,  half_sz],  # 2: Верхний правый
            [-half_sx,  half_sy,  half_sz],  # 3: Верхний левый
        ])
        for _ in range(4):
            normals.append([0.0, 0.0, 1.0])  # Нормаль вперед
        indices.extend([0, 1, 2, 0, 2, 3])
        
        # ЗАДНЯЯ ГРАНЬ
        base = len(vertices)
        vertices.extend([
            [-half_sx, -half_sy, -half_sz],  # 4
            [ half_sx, -half_sy, -half_sz],  # 5
            [ half_sx,  half_sy, -half_sz],  # 6
            [-half_sx,  half_sy, -half_sz],  # 7
        ])
        for _ in range(4):
            normals.append([0.0, 0.0, -1.0])  # Нормаль назад
        indices.extend([base, base+2, base+1, base, base+3, base+2])
        
        # ЛЕВАЯ ГРАНЬ
        base = len(vertices)
        vertices.extend([
            [-half_sx, -half_sy, -half_sz],  # 8
            [-half_sx, -half_sy,  half_sz],  # 9
            [-half_sx,  half_sy,  half_sz],  # 10
            [-half_sx,  half_sy, -half_sz],  # 11
        ])
        for _ in range(4):
            normals.append([-1.0, 0.0, 0.0])  # Нормаль влево
        indices.extend([base, base+1, base+2, base, base+2, base+3])
        
        # ПРАВАЯ ГРАНЬ
        base = len(vertices)
        vertices.extend([
            [ half_sx, -half_sy,  half_sz],  # 12
            [ half_sx, -half_sy, -half_sz],  # 13
            [ half_sx,  half_sy, -half_sz],  # 14
            [ half_sx,  half_sy,  half_sz],  # 15
        ])
        for _ in range(4):
            normals.append([1.0, 0.0, 0.0])  # Нормаль вправо
        indices.extend([base, base+1, base+2, base, base+2, base+3])
        
        # ВЕРХНЯЯ ГРАНЬ
        base = len(vertices)
        vertices.extend([
            [-half_sx,  half_sy,  half_sz],  # 16
            [ half_sx,  half_sy,  half_sz],  # 17
            [ half_sx,  half_sy, -half_sz],  # 18
            [-half_sx,  half_sy, -half_sz],  # 19
        ])
        for _ in range(4):
            normals.append([0.0, 1.0, 0.0])  # Нормаль вверх
        indices.extend([base, base+1, base+2, base, base+2, base+3])
        
        # НИЖНЯЯ ГРАНЬ
        base = len(vertices)
        vertices.extend([
            [-half_sx, -half_sy, -half_sz],  # 20
            [ half_sx, -half_sy, -half_sz],  # 21
            [ half_sx, -half_sy,  half_sz],  # 22
            [-half_sx, -half_sy,  half_sz],  # 23
        ])
        for _ in range(4):
            normals.append([0.0, -1.0, 0.0])  # Нормаль вниз
        indices.extend([base, base+1, base+2, base, base+2, base+3])
        
        # Преобразование в numpy массивы
        vertices_flat = np.array(vertices, dtype='f4').flatten()
        normals_flat = np.array(normals, dtype='f4').flatten()
        indices_flat = np.array(indices, dtype='i4')
        
        return vertices_flat, normals_flat, indices_flat
    
    def create_buffers(self):
        """Создание OpenGL буферов"""
        # VBO (Vertex Buffer Object) - буфер вершин
        self.vbo = self.ctx.buffer(self.vertices.tobytes())
        
        # NBO (Normal Buffer Object) - буфер нормалей
        self.nbo = self.ctx.buffer(self.normals.tobytes())
        
        # EBO (Element Buffer Object) - буфер индексов
        self.ebo = self.ctx.buffer(self.indices.tobytes())
        
        # VAO (Vertex Array Object) - массив вершин
        self.vao = self.ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'in_position'),  # Атрибут позиции
                (self.nbo, '3f', 'in_normal'),    # Атрибут нормали
            ],
            self.ebo  # Буфер индексов
        )
        
        # Количество индексов для рендеринга
        self.num_indices = len(self.indices)
    
    def render(self, program):
        """Рендеринг куба"""
        # Установка матрицы модели
        model_matrix = self.get_model_matrix()
        program['model'].write(model_matrix.tobytes())
        
        # Установка параметров материала
        self.set_material_uniforms(program)
        
        # Рендеринг с использованием индексов
        self.vao.render()

class Sphere(BaseObject):
    """Класс для создания сферы"""
    def __init__(self, ctx, program, position, radius, material, segments=32):
        super().__init__(ctx, program, position, material)
        
        self.radius = radius     # Радиус сферы
        self.segments = segments # Количество сегментов (качество)
        
        # Создание геометрии сферы
        self.vertices, self.normals, self.indices = self.create_sphere_geometry(radius, segments)
        
        # Создание OpenGL буферов
        self.create_buffers()
    
    def create_sphere_geometry(self, radius, segments):
        """Создание вершин, нормалей и индексов для сферы"""
        vertices = []
        normals = []
        
        # Генерация вершин
        for i in range(segments + 1):
            phi = np.pi * i / segments  # От 0 до π
            
            for j in range(segments + 1):
                theta = 2 * np.pi * j / segments  # От 0 до 2π
                
                # Координаты точки на сфере
                x = radius * np.sin(phi) * np.cos(theta)
                y = radius * np.cos(phi)
                z = radius * np.sin(phi) * np.sin(theta)
                
                # Нормаль (нормализованный вектор от центра)
                normal_x = np.sin(phi) * np.cos(theta)
                normal_y = np.cos(phi)
                normal_z = np.sin(phi) * np.sin(theta)
                
                vertices.append([x, y, z])
                normals.append([normal_x, normal_y, normal_z])
        
        # Генерация индексов
        indices = []
        for i in range(segments):
            for j in range(segments):
                # Индексы вершин квадрата
                v0 = i * (segments + 1) + j
                v1 = v0 + 1
                v2 = (i + 1) * (segments + 1) + j
                v3 = v2 + 1
                
                # Два треугольника на квадрат
                indices.extend([v0, v2, v1])
                indices.extend([v1, v2, v3])
        
        # Преобразование в numpy массивы
        vertices_flat = np.array(vertices, dtype='f4').flatten()
        normals_flat = np.array(normals, dtype='f4').flatten()
        indices_flat = np.array(indices, dtype='i4')
        
        return vertices_flat, normals_flat, indices_flat
    
    def create_buffers(self):
        """Создание OpenGL буферов для сферы"""
        self.vbo = self.ctx.buffer(self.vertices.tobytes())
        self.nbo = self.ctx.buffer(self.normals.tobytes())
        self.ebo = self.ctx.buffer(self.indices.tobytes())
        
        self.vao = self.ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'in_position'),
                (self.nbo, '3f', 'in_normal'),
            ],
            self.ebo
        )
        
        self.num_indices = len(self.indices)
    
    def render(self, program):
        """Рендеринг сферы"""
        model_matrix = self.get_model_matrix()
        program['model'].write(model_matrix.tobytes())
        
        self.set_material_uniforms(program)
        
        self.vao.render()