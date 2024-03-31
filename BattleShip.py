from __future__ import annotations
from typing import *
from enum import Enum


class Direction:
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __add__(self, other: Direction) -> Direction:
        return Direction(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> Direction:
        return Direction(self.x * other, self.y * other)


Diagonals = [Direction(1, 1), Direction(1, -1), Direction(-1, 1), Direction(-1, -1)]
Up = Direction(0, -1)
Down = Direction(0, 1)
Left = Direction(-1, 0)
Right = Direction(1, 0)


class Part(Enum):
    Start = 1
    End = 2
    FirstMiddle = 3
    SecondMiddle = 4
    NotShip = 5


class Value:
    is_ship: bool
    is_vertical: bool
    is_submarine: bool

    part: Part

    def __repr__(self):
        if self.is_submarine:
            return "S"
        elif self.is_ship:
            if self.is_vertical:
                if self.part == Part.Start:
                    return "^"
                elif self.part == Part.End:
                    return "v"
                elif self.part == Part.FirstMiddle:
                    return "|"
                else:
                    return "||"
            else:
                if self.part == Part.Start:
                    return "<"
                elif self.part == Part.End:
                    return ">"
                elif self.part == Part.FirstMiddle:
                    return "-"
                else:
                    return "--"
        else:
            return "."

    def __init__(self, is_ship: bool, is_vertical: bool, part: Part, is_submarine: bool = False):
        self.is_ship = is_ship
        self.is_vertical = is_vertical
        self.part = part
        self.is_submarine = is_submarine

    def is_horizontal(self) -> bool:
        return self.is_ship and not self.is_vertical and not self.is_submarine

    def is_vert(self) -> bool:
        return self.is_ship and self.is_vertical and not self.is_submarine

    def diagonal_invalid(self, other: Value) -> bool:
         return self.is_ship and other.is_ship

    def down_valid_helper(self, other: Value) -> bool:
        if not self.is_ship:
            return True

        if not self.is_vertical or self.part == Part.End or self.is_submarine:
            return not other.is_ship

        return self.valid_part(other)

    def up_valid_helper(self, other: Value) -> bool:
        if not self.is_ship:
            return True

        if not self.is_vertical or self.part == Part.Start or self.is_submarine:
            return not other.is_ship

        return other.valid_part(self)

    def valid_part(self, other: Value) -> bool:
        if not self.is_ship:
            return other.part == Part.Start
        if self.part == Part.Start:
            return other.part == Part.FirstMiddle or other.part == Part.End

        elif self.part == Part.FirstMiddle:
            return other.part == Part.SecondMiddle or other.part == Part.End

        elif self.part == Part.SecondMiddle:
            return other.part == Part.End

        return True

    def right_valid_helper(self, other: Value) -> bool:
        if not self.is_ship:
            return True

        if self.is_vertical or self.part == Part.End or self.is_submarine:
            return not other.is_ship

        return self.valid_part(other)

    def left_valid_helper(self, other: Value) -> bool:
        if not self.is_ship:
            return True

        if self.is_vertical or self.part == Part.Start or self.is_submarine:
            return not other.is_ship

        return other.valid_part(self)

    def up_invalid(self, other: Value) -> bool:
        return not (self.up_valid_helper(other) and other.down_valid_helper(self))

    def down_invalid(self, other: Value) -> bool:
        return not (self.down_valid_helper(other) and other.up_valid_helper(self))

    def left_invalid(self, other: Value) -> bool:
        return not (self.left_valid_helper(other) and other.right_valid_helper(self))

    def right_invalid(self, other: Value) -> bool:
        return not (self.right_valid_helper(other) and other.left_valid_helper(self))


submarine = Value(True, False, Part.NotShip, True)
vertical_ships = [Value(True, True, Part.Start), Value(True, True, Part.FirstMiddle),
                  Value(True, True, Part.SecondMiddle), Value(True, True, Part.End)]
horizontal_ships = [Value(True, False, Part.Start), Value(True, False, Part.FirstMiddle),
                    Value(True, False, Part.SecondMiddle), Value(True, False, Part.End)]
water = Value(False, False, Part.NotShip)

values: List[Value] = [submarine] + vertical_ships + horizontal_ships + [water]


class Variable:
    domain: List[Value]
    value: Optional[Value] = None

    def __init__(self):
        self.domain = values.copy()

    def __copy__(self):
        new = Variable()
        new.domain = self.domain.copy()
        new.value = self.value
        return new
    def __repr__(self):
        value = None
        if self.value:
            value = "".join([self.value.__repr__()])
        else:
            value = "".join([value.__repr__() for value in self.domain])

        to_pad = 10 - len(value)
        return " " * (to_pad // 2) + value + " " * (to_pad // 2)


class InvalidBoardException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Board:
    size: int
    board: List[List[Variable]]
    queue: List[Direction]
    submarine_pieces_remaining: int
    start_pieces_remaining: int
    end_pieces_remaining: int
    first_middle_pieces_remaining: int
    second_middle_pieces_remaining: int
    row_constraints: List[int]
    col_constraints: List[int]

    def __init__(self, size: int, board_str: Optional[List[List[str]]] = None, ship_sizes: List[int] = None,
                 row_constraints: List[int] = None, col_constraints: List[int] = None):
        self.row_constraints = row_constraints
        self.col_constraints = col_constraints
        if board_str:
            self.submarine_pieces_remaining = ship_sizes[0]
            self.start_pieces_remaining = ship_sizes[1] + ship_sizes[2] + ship_sizes[3]
            self.end_pieces_remaining = self.start_pieces_remaining
            self.first_middle_pieces_remaining = ship_sizes[2] + ship_sizes[3]
            self.second_middle_pieces_remaining = ship_sizes[3]
            self.size = size
            self.board = [[Variable() for _ in range(size)] for _ in range(size)]
            self.queue = []

            print("before handling edges\n", self)
            self.handle_edges()
            print("after handling edges\n", self)
            self.handle_ship_constraints()
            print("after handling ship constraints\n", self)
            self.handle_board_str(board_str)
            print("after handling board str\n", self)
            self.handle_check_for_row_col_sizes()
            print("after handling row col sizes\n", self)
            self.forward_check()
            print("after forward checking\n", self)

    def handle_check_for_row_col_sizes(self):
        for y in range(self.size):
            row_constraint = self.row_constraints[y]
            for x in range(self.size):
                if row_constraint == 1:
                    self.remove_from_domain_by_fun(Direction(x, y), lambda x: x.is_horizontal())
                if row_constraint == 2:
                    self.remove_from_domain_by_fun(Direction(x, y), lambda x: x.is_horizontal() and (x.part == Part.FirstMiddle or x.part == Part.SecondMiddle))
                if row_constraint == 3:
                     self.remove_from_domain(Direction(x, y), horizontal_ships[2])
        for x in range(self.size):
            col_constraint = self.col_constraints[x]
            for y in range(self.size):
                if col_constraint == 1:
                    self.remove_from_domain_by_fun(Direction(x, y), lambda x: x.is_vert())
                if col_constraint == 2:
                    self.remove_from_domain_by_fun(Direction(x, y), lambda x: x.is_vert() and (x.part == Part.FirstMiddle or x.part == Part.SecondMiddle))
                if col_constraint == 3:
                    self.remove_from_domain(Direction(x, y), vertical_ships[2])




    def handle_ship_constraints(self):
        if self.submarine_pieces_remaining == 0:
            self.remove_from_all_domains(submarine)

        if self.start_pieces_remaining == 0:
            self.remove_from_all_domains_by_fun(lambda x: x.part == Part.Start or x.part == Part.End)

        if self.first_middle_pieces_remaining == 0:
            self.remove_from_all_domains_by_fun(lambda x: x.part == Part.FirstMiddle)

        if self.second_middle_pieces_remaining == 0:
            self.remove_from_all_domains_by_fun(lambda x: x.part == Part.SecondMiddle)

    def handle_edges(self):
        for y in range(size):
            left_col = Direction(0, y)
            right_col = Direction(size - 1, y)
            top_row = Direction(y, 0)
            bottom_row = Direction(y, size - 1)
            self.remove_from_domain_by_fun(left_col, lambda x: (x.is_horizontal() and x.part != Part.Start))
            self.remove_from_domain_by_fun(right_col, lambda x: (x.is_horizontal() and x.part != Part.End))
            self.remove_from_domain_by_fun(top_row, lambda x: x.is_vert() and x.part != Part.Start)
            self.remove_from_domain_by_fun(bottom_row, lambda x: x.is_vert() and x.part != Part.End)


    def handle_board_str(self, board_str: List[List[str]]):
        for y in range(self.size):
            for x in range(self.size):
                location = Direction(x, y)
                str_val = board_str[y][x]
                if str_val == ".":
                    self.set(location, water)
                elif str_val == "S":
                    self.set(location, submarine)
                elif str_val == "<":
                    self.set(location, horizontal_ships[0])
                elif str_val == ">":
                    self.set(location, horizontal_ships[3])
                elif str_val == "v":
                    self.set(location, vertical_ships[3])
                elif str_val == "^":
                    self.set(location, vertical_ships[0])
                elif str_val == "M":
                    self[location].domain = [value for value in self[location].domain if
                                             (value.part == Part.FirstMiddle or value.part == Part.SecondMiddle)]

    def __copy__(self):
        new = Board(self.size)
        new.board = [[variable.__copy__() for variable in row] for row in self.board]
        new.queue = []
        new.row_constraints = self.row_constraints
        new.col_constraints = self.col_constraints
        new.submarine_pieces_remaining = self.submarine_pieces_remaining
        new.start_pieces_remaining = self.start_pieces_remaining
        new.end_pieces_remaining = self.end_pieces_remaining
        new.first_middle_pieces_remaining = self.first_middle_pieces_remaining
        new.second_middle_pieces_remaining = self.second_middle_pieces_remaining
        return new
    def find_shortest_domain(self) -> Optional[Direction]:
        shortest = 30
        shortest_location = None
        for y in range(self.size):
            for x in range(self.size):
                location = Direction(x, y)
                item = self[location]
                if item.value is None and len(item.domain) < shortest:
                    shortest = len(item.domain)
                    shortest_location = location

        return shortest_location
    def backtracking_search(self) -> Optional[Board]:

        location = self.find_shortest_domain()
        if location is None:
            return self
        item = self[location]
        for value in item.domain:
            try:
                new_board = self.__copy__()
                new_board.set(location, value)
                new_board.forward_check()
                return new_board.backtracking_search()
            except InvalidBoardException:
                continue
            except Exception as e:
                raise e



    def forward_check(self):
        self.run_queue()
        self.check_row_and_col_constraints()
        if self.queue:
            self.forward_check()



    def check_row_and_col_constraints(self):
        for y in range(self.size):
            for x in range(self.size):
                count = 0
                location = Direction(x, y)
                item = self[location]
                if item.value != None and item.value != water:
                    count += 1
                elif item.value == None and water not in item.domain:
                    count += 1
            if count > self.row_constraints[y]:
                raise InvalidBoardException("Invalid board")
            elif count == self.row_constraints[y]:
                for x in range(self.size):
                    if self[Direction(x, y)].value is None:
                        self.set(Direction(x, y), water)
        for x in range(self.size):
            for y in range(self.size):
                count = 0
                location = Direction(x, y)
                item = self[location]
                if item.value != None and item.value != water:
                    count += 1
                elif item.value == None and water not in item.domain:
                    count += 1
            if count > self.col_constraints[x]:
                raise InvalidBoardException("Invalid board")
            elif count == self.col_constraints[x]:
                for y in range(self.size):
                    if self[Direction(x, y)].value is None:
                        self.set(Direction(x, y), water)

    def __repr__(self):
        return "\n".join([row.__repr__() for row in self.board]) + "\n"

    def __getitem__(self, item: Direction):
        if item.x < 0 or item.x >= self.size or item.y < 0 or item.y >= self.size:
            return None
        else:
            return self.board[item.y][item.x]

    def remove_from_domain(self, location: Direction, value: Value):
        self.remove_from_domain_by_fun(location, lambda x: x == value)

    def remove_from_domain_by_fun(self, location: Direction, fun: Callable[[Value], bool]):

        item = self[location]
        if item is None:
            return
        previous_len = len(item.domain)
        item.domain = [value for value in item.domain if not fun(value)]
        if len(item.domain) == 1 and previous_len != 1:
            self.queue.append(location)
        elif len(item.domain) == 0:
            raise InvalidBoardException("Invalid board")

    def remove_from_all_domains(self, value: Value):
        for x in range(self.size):
            for y in range(self.size):
                self.remove_from_domain(Direction(x, y), value)

    def remove_from_all_domains_by_fun(self, fun: Callable[[Value], bool]):
        for x in range(self.size):
            for y in range(self.size):
                self.remove_from_domain_by_fun(Direction(x, y), fun)

    def add_ship_piece(self, value: Value):
        if not value.is_ship:
            return
        if value.is_submarine:
            self.submarine_pieces_remaining -= 1
            if self.submarine_pieces_remaining == 0:
                self.remove_from_all_domains(submarine)
        elif value.part == Part.Start:
            self.start_pieces_remaining -= 1
            if self.start_pieces_remaining == 0:
                self.remove_from_all_domains(vertical_ships[0])
                self.remove_from_all_domains(horizontal_ships[0])
        elif value.part == Part.FirstMiddle:
            self.first_middle_pieces_remaining -= 1
            if self.first_middle_pieces_remaining == 0:
                self.remove_from_all_domains(vertical_ships[1])
                self.remove_from_all_domains(horizontal_ships[1])
        elif value.part == Part.SecondMiddle:
            self.second_middle_pieces_remaining -= 1
            if self.second_middle_pieces_remaining == 0:
                self.remove_from_all_domains(vertical_ships[2])
                self.remove_from_all_domains(horizontal_ships[2])
        elif value.part == Part.End:
            self.end_pieces_remaining -= 1
            if self.end_pieces_remaining == 0:
                self.remove_from_all_domains(vertical_ships[3])
                self.remove_from_all_domains(horizontal_ships[3])

    def set(self, location: Direction, value: Value):
        item = self[location]
        if value not in item.domain:
            raise Exception("Invalid value")

        item.value = value
        for direction in Diagonals:
            self.remove_from_domain_by_fun(location + direction, value.diagonal_invalid)

        self.remove_from_domain_by_fun(location + Up, value.up_invalid)
        self.remove_from_domain_by_fun(location + Down, value.down_invalid)
        self.remove_from_domain_by_fun(location + Left, value.left_invalid)

    # def compare(self, location: Direction
    #             , compare_function: Callable[[Value], bool]):
    #     item2 = self[location]
    #     if item2 is None:
    #         return
    #     new_domain = []
    #     if item2.value:
    #         return compare_function(item2.value)
    #
    #     for domain_value in item2.domain:
    #         if compare_function(domain_value):
    #             new_domain.append(domain_value)
    #     if new_domain:
    #         if len(new_domain) == 1:
    #             self.queue.append(location)
    #         item2.domain = new_domain
    #
    #         return True
    #
    #     else:
    #         return False

    def run_queue(self):
        while self.queue:
            location = self.queue.pop()
            if self[location].value:
                continue

            if len(self[location].domain) != 1:
                raise Exception("Invalid domain")

            self.set(location, self[location].domain[0])


if __name__ == '__main__':
    file = open("hard2.txt", "r")
    board_str = file.read().splitlines()
    board_str = [list(row) for row in board_str]
    sizes = [int(x) for x in board_str[2]]
    row_constraints = [int(x) for x in board_str[0]]
    col_constraints = [int(x) for x in board_str[1]]
    size = len(board_str[0])
    board_str = board_str[3:]
    board = Board(size, board_str, sizes, row_constraints, col_constraints)
    print(board)
    print(board[Direction(3, 0)].value)
