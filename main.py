import pygame
import random
from typing import List, Tuple, Dict, Optional

# Инициализация pygame
pygame.init()

# Константы
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
CARD_WIDTH = 71
CARD_HEIGHT = 96
CARD_GAP = 20
CARD_GAP_STACK = 30
MARGIN = 20

# Цвета
GREEN = (0, 100, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Типы карт
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


class Card:
    """Класс для представления игральной карты."""

    def __init__(self, suit: str, rank: str, face_up: bool = False):
        self.suit = suit
        self.rank = rank
        self.face_up = face_up
        self.color = RED if suit in ['hearts', 'diamonds'] else BLACK
        self.position = (0, 0)

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"

    def draw(self, screen: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Отрисовка карты на экране с тенью и оконтовкой."""
        shadow_pos = (pos[0]+2, pos[1]+2)  # Смещение для тени
        self.position = pos

        # Рисуем тень (только для видимых карт)
        if self.face_up or not self.face_up:  # Тень для всех карт
            pygame.draw.rect(screen, (50, 50, 50), (*shadow_pos, CARD_WIDTH, CARD_HEIGHT), 0, 5)

        if self.face_up:
            # Лицевая сторона с двойной оконтовкой
            pygame.draw.rect(screen, BLACK, (*pos, CARD_WIDTH, CARD_HEIGHT), 0, 5)
            pygame.draw.rect(screen, WHITE, (pos[0]+2, pos[1]+2, CARD_WIDTH-4, CARD_HEIGHT-4), 0, 5)

            # Текст
            font = pygame.font.SysFont('Arial', 20)
            text = font.render(self.rank, True, self.color)
            screen.blit(text, (pos[0] + 5, pos[1] + 5))

            # Масть в углу
            small_font = pygame.font.SysFont('Arial', 14)
            suit_text = small_font.render(self.suit[0].upper(), True, self.color)  # Первая буква масти
            screen.blit(suit_text, (pos[0] + CARD_WIDTH - 15, pos[1] + CARD_HEIGHT - 20))
        else:
            # Рубашка с двойной оконтовкой
            pygame.draw.rect(screen, BLACK, (*pos, CARD_WIDTH, CARD_HEIGHT), 0, 5)
            pygame.draw.rect(screen, BLUE, (pos[0]+2, pos[1]+2, CARD_WIDTH-4, CARD_HEIGHT-4), 0, 5)

            # Узор на рубашке
            pygame.draw.rect(screen, WHITE, (pos[0]+5, pos[1]+5, CARD_WIDTH-10, CARD_HEIGHT-10), 2, 5)
            pygame.draw.line(screen, WHITE, (pos[0]+10, pos[1]+10),
                             (pos[0]+CARD_WIDTH-10, pos[1]+CARD_HEIGHT-10), 2)
            pygame.draw.line(screen, WHITE, (pos[0]+CARD_WIDTH-10, pos[1]+10),
                             (pos[0]+10, pos[1]+CARD_HEIGHT-10), 2)


class Solitaire:
    """Класс для реализации игры 'Косынка'."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Косынка")
        self.clock = pygame.time.Clock()

        # Создаем колоду карт
        self.deck = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)

        # Инициализация стопок
        self.stock: List[Card] = []
        self.waste: List[Card] = []
        self.foundations: Dict[str, List[Card]] = {suit: [] for suit in SUITS}
        self.tableau: List[List[Card]] = [[] for _ in range(7)]
        self.selected_cards: Optional[List[Card]] = None
        self.selected_stack: Optional[str] = None
        self.drag_pos: Optional[Tuple[int, int]] = None

        # Раздача карт в tableau
        for i in range(7):
            for j in range(i + 1):
                card = self.deck.pop()
                card.face_up = (j == i)  # Последняя карта в каждой стопке открыта
                self.tableau[i].append(card)

        # Оставшиеся карты идут в сток
        self.stock = self.deck.copy()

    def reset_game(self) -> None:
        """Сбрасывает игру в начальное состояние."""
        self.__init__()

    def draw_game(self) -> None:
        """Отрисовка всех элементов игры."""
        self.screen.fill(GREEN)

        # Рисуем сток и отбой
        self.draw_stock_and_waste()

        # Рисуем фундаменты (дома)
        self.draw_foundations()

        # Рисуем tableau (игровые стопки)
        self.draw_tableau()

        # Рисуем перетаскиваемые карты
        if self.selected_cards and self.drag_pos:
            dx, dy = self.drag_pos
            for i, card in enumerate(self.selected_cards):
                card.draw(self.screen, (dx, dy + i * CARD_GAP // 2))

        pygame.display.flip()

    def has_possible_moves(self) -> bool:
        """Проверяет, есть ли возможные ходы в текущей позиции."""
        # 1. Проверяем ходы из отбоя (waste)
        if self.waste:
            top_waste = self.waste[-1]
            # Можно ли положить в фундамент?
            if self.can_move_to_foundation(top_waste):
                return True
            # Можно ли положить в tableau?
            for i in range(7):
                if self.can_move_to_tableau(top_waste, i):
                    return True

        # 2. Проверяем ходы из tableau
        for i, pile in enumerate(self.tableau):
            if not pile:
                continue

            # Находим первую открытую карту в стопке
            open_cards = [card for card in pile if card.face_up]
            if not open_cards:
                continue

            top_tableau_card = open_cards[-1]  # Берем самую верхнюю открытую

            # Можно ли положить в фундамент?
            if self.can_move_to_foundation(top_tableau_card):
                return True

            # Можно ли переместить в другую стопку tableau?
            for j in range(7):
                if i == j:
                    continue  # Не проверяем перемещение в ту же стопку
                if self.can_move_to_tableau(top_tableau_card, j):
                    return True

        # 3. Проверяем можно ли взять карту из стока
        if self.stock or (not self.stock and self.waste):
            return True

        # 4. Проверяем можно ли переместить карты между стопками tableau
        for i, pile in enumerate(self.tableau):
            if len(pile) <= 1:
                continue

            # Ищем последовательности карт, которые можно переместить
            open_cards = [card for card in pile if card.face_up]
            if len(open_cards) < 2:
                continue

            # Проверяем можно ли переместить последовательность в другую стопку
            for j in range(7):
                if i == j:
                    continue
                if self.can_move_to_tableau(open_cards[0], j):
                    return True

        return False

    def draw_stock_and_waste(self) -> None:
        """Отрисовка стока и отбоя."""
        # Сток
        stock_pos = (MARGIN, MARGIN)
        if self.stock:
            pygame.draw.rect(self.screen, WHITE, (*stock_pos, CARD_WIDTH, CARD_HEIGHT), 0, 5)
            pygame.draw.rect(self.screen, BLACK, (*stock_pos, CARD_WIDTH, CARD_HEIGHT), 2, 5)
        else:
            pygame.draw.rect(self.screen, GREEN, (*stock_pos, CARD_WIDTH, CARD_HEIGHT), 2, 5)

        # Отбой
        waste_pos = (MARGIN + CARD_WIDTH + MARGIN, MARGIN)
        if self.waste:
            self.waste[-1].draw(self.screen, waste_pos)

    def draw_foundations(self) -> None:
        """Отрисовка фундаментов (домов)."""
        for i, suit in enumerate(SUITS):
            pos = (MARGIN * 3 + CARD_WIDTH * 3 + i * (CARD_WIDTH + MARGIN), MARGIN)
            if self.foundations[suit]:
                self.foundations[suit][-1].draw(self.screen, pos)
            else:
                pygame.draw.rect(self.screen, GREEN, (*pos, CARD_WIDTH, CARD_HEIGHT), 2, 5)

    def draw_tableau(self) -> None:
        """Отрисовка игровых стопок (tableau)."""
        for i, pile in enumerate(self.tableau):
            for j, card in enumerate(pile):
                pos = (MARGIN + i * (CARD_WIDTH + MARGIN),
                       MARGIN * 2 + CARD_HEIGHT + j * CARD_GAP_STACK)
                card.draw(self.screen, pos)

    def deal_from_stock(self) -> None:
        """Взять карты из стока в отбой."""
        if self.stock:
            card = self.stock.pop()
            card.face_up = True
            self.waste.append(card)
        else:
            # Если сток пуст, переворачиваем отбой обратно в сток
            self.stock = self.waste[::-1]
            for card in self.stock:
                card.face_up = False
            self.waste = []

    def get_card_at_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[Card, str, int]]:
        """Получить карту по позиции на экране."""
        x, y = pos

        # Проверяем отбой
        waste_pos = (MARGIN + CARD_WIDTH + MARGIN, MARGIN)
        if (waste_pos[0] <= x <= waste_pos[0] + CARD_WIDTH and
                waste_pos[1] <= y <= waste_pos[1] + CARD_HEIGHT and
                self.waste):
            return (self.waste[-1], 'waste', -1)

        # Проверяем tableau
        for i, pile in enumerate(self.tableau):
            if pile:
                last_card_pos = (MARGIN + i * (CARD_WIDTH + MARGIN),
                                 MARGIN * 2 + CARD_HEIGHT + (len(pile) - 1) * CARD_GAP_STACK)
                if (last_card_pos[0] <= x <= last_card_pos[0] + CARD_WIDTH and
                        last_card_pos[1] <= y <= last_card_pos[1] + CARD_HEIGHT):
                    return (pile[-1], 'tableau', i)

        return None

    def get_cards_from_tableau(self, pile_idx: int, card: Card) -> Optional[List[Card]]:
        """Получить карты из tableau начиная с указанной."""
        pile = self.tableau[pile_idx]
        if card in pile:
            idx = pile.index(card)
            return pile[idx:]
        return None

    def can_move_to_foundation(self, card: Card) -> bool:
        """Можно ли переместить карту в фундамент."""
        foundation = self.foundations[card.suit]
        if card.rank == 'A' and not foundation:
            return True
        elif foundation:
            last_card = foundation[-1]
            current_idx = RANKS.index(card.rank)
            last_idx = RANKS.index(last_card.rank)
            return current_idx == last_idx + 1
        return False

    def can_move_to_tableau(self, card: Card, pile_idx: int) -> bool:
        """Можно ли переместить карту в указанную стопку tableau."""
        pile = self.tableau[pile_idx]
        if not pile:
            return card.rank == 'K'
        else:
            top_card = pile[-1]
            return (card.color != top_card.color and
                    RANKS.index(card.rank) == RANKS.index(top_card.rank) - 1)

    def move_to_foundation(self, card: Card) -> bool:
        """Переместить карту в фундамент."""
        if self.can_move_to_foundation(card):
            # Удаляем карту из текущего места
            if self.selected_stack == 'waste' and self.waste and self.waste[-1] == card:
                self.waste.pop()
            elif self.selected_stack == 'tableau' and self.selected_cards:
                pile_idx = self.tableau.index(self.selected_cards[0].position[0] // (CARD_WIDTH + MARGIN))
                for c in self.selected_cards:
                    if c in self.tableau[pile_idx]:
                        self.tableau[pile_idx].remove(c)

            # Добавляем в фундамент
            self.foundations[card.suit].append(card)
            return True
        return False

    def move_to_tableau(self, cards: List[Card], pile_idx: int) -> bool:
        """Переместить карты в указанную стопку tableau."""
        if not cards:
            return False

        first_card = cards[0]
        if self.can_move_to_tableau(first_card, pile_idx):
            # Удаляем карты из текущего места
            if self.selected_stack == 'waste' and self.waste and self.waste[-1] == first_card and len(cards) == 1:
                self.waste.pop()
            elif self.selected_stack == 'tableau' and self.selected_cards:
                # Находим исходную стопку, проверяя в какой стопке находится первая карта
                source_pile_idx = None
                for i, pile in enumerate(self.tableau):
                    if cards[0] in pile:
                        source_pile_idx = i
                        break

                if source_pile_idx is not None:
                    for c in self.selected_cards:
                        if c in self.tableau[source_pile_idx]:
                            self.tableau[source_pile_idx].remove(c)

            # Добавляем в целевую стопку
            self.tableau[pile_idx].extend(cards)

            # Открываем последнюю карту в исходной стопке, если нужно
            if self.selected_stack == 'tableau' and source_pile_idx is not None and source_pile_idx != pile_idx:
                if self.tableau[source_pile_idx] and not self.tableau[source_pile_idx][-1].face_up:
                    self.tableau[source_pile_idx][-1].face_up = True
            return True
        return False

    def check_win(self) -> bool:
        """Проверка, выиграна ли игра."""
        for suit in SUITS:
            if len(self.foundations[suit]) != len(RANKS):
                return False
        return True

    def handle_click(self, pos: Tuple[int, int]) -> None:
        """Обработка клика мыши."""
        x, y = pos

        # Проверяем клик по стоку
        stock_pos = (MARGIN, MARGIN)
        if (stock_pos[0] <= x <= stock_pos[0] + CARD_WIDTH and
                stock_pos[1] <= y <= stock_pos[1] + CARD_HEIGHT):
            self.deal_from_stock()
            return

        # Проверяем клик по отбою
        waste_pos = (MARGIN + CARD_WIDTH + MARGIN, MARGIN)
        if (waste_pos[0] <= x <= waste_pos[0] + CARD_WIDTH and
                waste_pos[1] <= y <= waste_pos[1] + CARD_HEIGHT and
                self.waste):
            self.selected_cards = [self.waste[-1]]
            self.selected_stack = 'waste'
            self.drag_pos = (x - CARD_WIDTH // 2, y - CARD_HEIGHT // 2)
            return

        # Проверяем клик по tableau
        for i, pile in enumerate(self.tableau):
            if not pile:
                continue

            # Проверяем клик по последней карте в стопке
            last_card_pos = (MARGIN + i * (CARD_WIDTH + MARGIN),
                             MARGIN * 2 + CARD_HEIGHT + (len(pile) - 1) * CARD_GAP_STACK)
            if (last_card_pos[0] <= x <= last_card_pos[0] + CARD_WIDTH and
                    last_card_pos[1] <= y <= last_card_pos[1] + CARD_HEIGHT):
                clicked_card = pile[-1]
                if clicked_card.face_up:
                    self.selected_cards = [clicked_card]
                    self.selected_stack = 'tableau'
                    self.drag_pos = (x - CARD_WIDTH // 2, y - CARD_HEIGHT // 2)
                return

            # Проверяем клик по другим картам в стопке
            for j, card in enumerate(pile):
                if not card.face_up:
                    continue

                card_pos = (MARGIN + i * (CARD_WIDTH + MARGIN),
                            MARGIN * 2 + CARD_HEIGHT + j * CARD_GAP_STACK)
                if (card_pos[0] <= x <= card_pos[0] + CARD_WIDTH and
                        card_pos[1] <= y <= card_pos[1] + CARD_HEIGHT):
                    self.selected_cards = pile[j:]
                    self.selected_stack = 'tableau'
                    self.drag_pos = (x - CARD_WIDTH // 2, y - CARD_HEIGHT // 2)
                    return

    def handle_drop(self, pos: Tuple[int, int]) -> None:
        """Обработка отпускания карты (после перетаскивания)."""
        if not self.selected_cards or not self.selected_stack:
            return

        x, y = pos

        # Проверяем сброс на фундамент
        for i, suit in enumerate(SUITS):
            foundation_pos = (MARGIN * 3 + CARD_WIDTH * 3 + i * (CARD_WIDTH + MARGIN), MARGIN)
            if (foundation_pos[0] <= x <= foundation_pos[0] + CARD_WIDTH and
                    foundation_pos[1] <= y <= foundation_pos[1] + CARD_HEIGHT):
                if len(self.selected_cards) == 1 and self.move_to_foundation(self.selected_cards[0]):
                    self.selected_cards = None
                    self.selected_stack = None
                    self.drag_pos = None
                    return

        # Проверяем сброс на tableau
        for i in range(7):
            pile_pos_x = MARGIN + i * (CARD_WIDTH + MARGIN)
            pile_pos_y = MARGIN * 2 + CARD_HEIGHT

            # Если стопка пуста, проверяем сброс короля
            if not self.tableau[i]:
                if (pile_pos_x <= x <= pile_pos_x + CARD_WIDTH and
                        pile_pos_y <= y <= pile_pos_y + CARD_HEIGHT and
                        self.selected_cards[0].rank == 'K'):
                    self.move_to_tableau(self.selected_cards, i)
                    self.selected_cards = None
                    self.selected_stack = None
                    self.drag_pos = None
                    return
            else:
                # Проверяем сброс на последнюю карту в стопке
                last_card_pos = (pile_pos_x,
                                 pile_pos_y + (len(self.tableau[i]) - 1) * CARD_GAP_STACK)
                if (last_card_pos[0] <= x <= last_card_pos[0] + CARD_WIDTH and
                        last_card_pos[1] <= y <= last_card_pos[1] + CARD_HEIGHT):
                    if self.move_to_tableau(self.selected_cards, i):
                        self.selected_cards = None
                        self.selected_stack = None
                        self.drag_pos = None
                        return

        # Если сброс не на допустимую цель, сбрасываем выделение
        self.selected_cards = None
        self.selected_stack = None
        self.drag_pos = None

    def show_game_over_message(self) -> bool:
        """Показывает сообщение о конце игры и спрашивает, начать заново."""
        font = pygame.font.SysFont('Arial', 36)
        text = font.render("Нет возможных ходов!", True, WHITE)
        restart_text = font.render("Начать заново? (Y/N)", True, WHITE)

        # Создаем полупрозрачную поверхность
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))  # Черный с прозрачностью
        self.screen.blit(s, (0, 0))

        # Отображаем текст
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 10))
        pygame.display.flip()

        # Ждем ответа пользователя
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        return True
                    elif event.key == pygame.K_n:
                        return False
            self.clock.tick(30)

        return False

    def show_message(self, text: str) -> None:
        """Отображает сообщение поверх игры."""
        # Создаем полупрозрачное затемнение
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))

        # Отображаем текст
        font = pygame.font.SysFont('Arial', 36)
        text_surface = font.render(text, True, WHITE)
        self.screen.blit(text_surface,
                         (SCREEN_WIDTH//2 - text_surface.get_width()//2,
                          SCREEN_HEIGHT//2 - text_surface.get_height()//2))

        pygame.display.flip()

    def run(self) -> None:
        """Основной игровой цикл."""
        running = True
        game_over = False
        show_message = False
        message_text = ""

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    if event.button == 1:  # Левая кнопка мыши
                        self.handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and not game_over:
                    if event.button == 1 and self.selected_cards:
                        self.handle_drop(event.pos)
                elif event.type == pygame.MOUSEMOTION and not game_over:
                    if self.selected_cards and self.drag_pos:
                        self.drag_pos = (event.pos[0] - CARD_WIDTH//2,
                                         event.pos[1] - CARD_HEIGHT//2)
                elif event.type == pygame.KEYDOWN and show_message:
                    if event.key == pygame.K_y:
                        self.reset_game()
                        game_over = False
                        show_message = False
                    elif event.key == pygame.K_n:
                        running = False

            # Основная отрисовка игры
            self.draw_game()

            # Проверяем условия конца игры (только если не в режиме сообщения)
            if not game_over and not show_message:
                if self.check_win():
                    message_text = "Поздравляем! Вы выиграли! Начать заново? (Y/N)"
                    game_over = True
                    show_message = True
                elif not self.has_possible_moves():
                    message_text = "Нет возможных ходов! Начать заново? (Y/N)"
                    game_over = True
                    show_message = True

            # Показываем сообщение (если нужно)
            if show_message:
                self.show_message(message_text)

            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Solitaire()
    game.run()
