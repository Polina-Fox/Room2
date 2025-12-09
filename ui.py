"""
Графический интерфейс пользователя (UI)
"""

import pygame

class Button:
    """Класс кнопки интерфейса"""
    def __init__(self, x, y, width, height, text, action=None):
        # Прямоугольник кнопки
        self.rect = pygame.Rect(x, y, width, height)
        
        # Текст кнопки
        self.text = text
        
        # Действие при нажатии
        self.action = action
        
        # Цвета
        self.color = (70, 70, 90)           # Обычный цвет
        self.hover_color = (90, 90, 110)    # Цвет при наведении
        self.text_color = (255, 255, 255)   # Цвет текста
        
        # Шрифт
        self.font = pygame.font.SysFont('Arial', 16)
        
        # Флаг наведения мыши
        self.hovered = False
    
    def draw(self, surface):
        """Отрисовка кнопки"""
        # Выбор цвета в зависимости от состояния
        color = self.hover_color if self.hovered else self.color
        
        # Рисование фона кнопки
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        # Рисование рамки
        pygame.draw.rect(surface, (40, 40, 60), self.rect, 2, border_radius=5)
        
        # Создание текста
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        
        # Отрисовка текста
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        """Проверка, находится ли курсор над кнопкой"""
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    
    def check_click(self, pos):
        """Проверка клика по кнопке"""
        if self.rect.collidepoint(pos):
            return self.action  # Возвращаем действие кнопки
        return None

class UI:
    """Класс графического интерфейса"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Шрифты
        self.font = pygame.font.SysFont('Arial', 18)      # Основной шрифт
        self.small_font = pygame.font.SysFont('Arial', 14) # Мелкий шрифт
        
        # Список кнопок
        self.buttons = []
        
        # Параметры панели
        self.panel_width = 300          # Ширина панели
        self.panel_height = height      # Высота панели
        self.panel_color = (30, 30, 40, 200)  # Цвет панели (полупрозрачный)
        
        # Создание элементов управления
        self.create_controls()
    
    def create_controls(self):
        """Создание элементов управления интерфейса"""
        x_offset = 20      # Отступ слева
        y_offset = 50      # Отступ сверху
        button_width = 250 # Ширина кнопок
        button_height = 30 # Высота кнопок
        spacing = 10       # Расстояние между кнопками
        
        # ЗАГОЛОВОК
        self.title_rect = pygame.Rect(x_offset, 10, button_width, 30)
        
        # КНОПКИ ДЛЯ УПРАВЛЕНИЯ ОБЪЕКТАМИ
        objects = [
            ('cube1', 'Большой куб'),
            ('cube2', 'Голубой куб'),
            ('sphere1', 'Пурпурная сфера'),
            ('sphere2', 'Оранжевая сфера')
        ]
        
        for i, (obj_id, obj_name) in enumerate(objects):
            # Кнопка для включения/выключения зеркальности
            self.buttons.append(Button(
                x_offset, 
                y_offset + i*(button_height+spacing)*2,
                button_width, 
                button_height,
                f"Зеркальность: {obj_name}",
                f"toggle_mirror_{obj_id}"
            ))
            
            # Кнопка для включения/выключения прозрачности
            self.buttons.append(Button(
                x_offset, 
                y_offset + i*(button_height+spacing)*2 + button_height + spacing//2,
                button_width, 
                button_height,
                f"Прозрачность: {obj_name}",
                f"toggle_transparent_{obj_id}"
            ))
        
        # Смещение для следующей группы кнопок
        y_offset += len(objects)*(button_height+spacing)*2 + 20
        
        # ВЫБОР ЗЕРКАЛЬНОЙ СТЕНЫ
        walls = [
            ('none', 'Нет зеркальной стены'),
            ('left', 'Левая стена (красная)'),
            ('right', 'Правая стена (зеленая)'),
            ('back', 'Задняя стена'),
            ('floor', 'Пол'),
            ('ceiling', 'Потолок')
        ]
        
        for i, (wall_id, wall_name) in enumerate(walls):
            self.buttons.append(Button(
                x_offset, 
                y_offset + i*(button_height+spacing),
                button_width, 
                button_height,
                wall_name,
                f"mirror_wall_{wall_id}"
            ))
        
        y_offset += len(walls)*(button_height+spacing) + 20
        
        # УПРАВЛЕНИЕ СВЕТОМ
        self.buttons.append(Button(
            x_offset, y_offset,
            button_width, button_height,
            "Вкл/Выкл свет 1",
            "toggle_light1"
        ))
        
        self.buttons.append(Button(
            x_offset, y_offset + button_height + spacing,
            button_width, button_height,
            "Вкл/Выкл свет 2",
            "toggle_light2"
        ))
        
        self.buttons.append(Button(
            x_offset, y_offset + (button_height + spacing)*2,
            button_width, button_height,
            "Сменить перемещаемый свет",
            "switch_moving_light"
        ))
        
        y_offset += (button_height + spacing)*3 + 20
        
        # ДОПОЛНИТЕЛЬНЫЕ КНОПКИ
        self.buttons.append(Button(
            x_offset, y_offset,
            button_width, button_height,
            "Сброс камеры",
            "reset_camera"
        ))
        
        self.buttons.append(Button(
            x_offset, y_offset + button_height + spacing,
            button_width, button_height,
            "Скрыть/показать UI (U)",
            "toggle_ui"
        ))
    
    def update(self, object_states, lights, moving_light_index, mirror_wall):
        """Обновление текста кнопок на основе состояний"""
        for button in self.buttons:
            # ОБНОВЛЕНИЕ КНОПОК ЗЕРКАЛЬНОСТИ
            if button.action and button.action.startswith('toggle_mirror_'):
                obj_id = button.action.replace('toggle_mirror_', '')
                if obj_id in object_states:
                    # Определяем текущее состояние
                    state = "ВКЛ" if object_states[obj_id]['mirror'] else "ВЫКЛ"
                    button.text = f"Зеркальность {obj_id}: {state}"
            
            # ОБНОВЛЕНИЕ КНОПОК ПРОЗРАЧНОСТИ
            elif button.action and button.action.startswith('toggle_transparent_'):
                obj_id = button.action.replace('toggle_transparent_', '')
                if obj_id in object_states:
                    state = "ВКЛ" if object_states[obj_id]['transparent'] else "ВЫКЛ"
                    button.text = f"Прозрачность {obj_id}: {state}"
            
            # ОБНОВЛЕНИЕ КНОПОК ЗЕРКАЛЬНОЙ СТЕНЫ
            elif button.action and button.action.startswith('mirror_wall_'):
                wall_id = button.action.replace('mirror_wall_', '')
                # Подсветка выбранной стены
                if mirror_wall == wall_id:
                    button.color = (100, 150, 200)  # Голубой для выбранной
                else:
                    button.color = (70, 70, 90)     # Серый для невыбранной
            
            # ОБНОВЛЕНИЕ КНОПОК СВЕТА
            elif button.action == 'toggle_light1':
                state = "ВКЛ" if lights[0]['enabled'] else "ВЫКЛ"
                button.text = f"Свет 1: {state}"
            
            elif button.action == 'toggle_light2':
                state = "ВКЛ" if lights[1]['enabled'] else "ВЫКЛ"
                button.text = f"Свет 2: {state}"
            
            elif button.action == 'switch_moving_light':
                light_name = lights[moving_light_index]['name']
                button.text = f"Перемещаемый: {light_name}"
    
    def handle_event(self, event):
        """Обработка событий интерфейса"""
        # ДВИЖЕНИЕ МЫШИ
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)  # Проверка наведения
        
        # НАЖАТИЕ КНОПКИ МЫШИ
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                for button in self.buttons:
                    action = button.check_click(event.pos)
                    if action:
                        return action  # Возвращаем действие кнопки
        
        return None  # Если ничего не нажато
    
    def render(self, surface):
        """Отрисовка интерфейса"""
        # ПОЛУПРОЗРАЧНАЯ ПАНЕЛЬ
        panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.panel_color)
        surface.blit(panel_surface, (0, 0))
        
        # ЗАГОЛОВОК
        title = self.font.render("Панель управления Cornell Box", True, (255, 255, 255))
        surface.blit(title, (20, 15))
        
        # ИНСТРУКЦИИ
        instructions = [
            "Управление мышью:",
            "- ЛКМ: вращение камеры",
            "- ПКМ: смещение камеры",
            "- Колесико: приближение",
            "",
            "Управление светом:",
            "- WASD/QE: перемещение света",
            "- +/-: интенсивность света",
            "- TAB: выбор света",
            "",
            "Клавиши:",
            "- U: показать/скрыть UI",
            "- R: сброс камеры",
            "- ESC: выход"
        ]
        
        # Отрисовка инструкций
        y_pos = 400
        for line in instructions:
            text = self.small_font.render(line, True, (200, 200, 220))
            surface.blit(text, (20, y_pos))
            y_pos += 20
        
        # ОТРИСОВКА ВСЕХ КНОПОК
        for button in self.buttons:
            button.draw(surface)