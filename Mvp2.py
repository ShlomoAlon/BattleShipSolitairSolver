from __future__ import annotations

import copy
import textwrap
import time
from dataclasses import dataclass
from typing import *


@dataclass
class Location:
    x: int
    y: int

    def __add__(self, other: Location) -> Location:
        return Location(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> Location:
        return Location(self.x * other, self.y * other)


@dataclass
class Ship:
    start: Location
    size: int
    vertical: bool

    def ship_string(self) -> str:
        if self.size == 1:
            return textwrap.dedent("""\
                ...
                .S.
                ...""")
        if self.vertical:
            if self.size == 2:
                return textwrap.dedent("""\
                    ...
                    .^.
                    .v.
                    ...""")
            if self.size == 3:
                return textwrap.dedent("""\
                    ...
                    .^.
                    .M.
                    .v.
                    ...""")
            if self.size == 4:
                return textwrap.dedent("""\
                    ...
                    .^.
                    .M.
                    .M.
                    .v.
                    ...""")
        else:
            if self.size == 2:
                return textwrap.dedent("""\
                    ....
                    .<>.
                    ....""")
            if self.size == 3:
                return textwrap.dedent("""\
                    .....
                    .<M>.
                    .....""")
            if self.size == 4:
                return textwrap.dedent("""\
                    ......
                    .<MM>.
                    ......""")


class ControlFlowError(Exception):
    pass


class Board:
    board_representation: List[List[str]]
    row_constraints: List[int]
    row_constraints_water: List[int]
    col_constraints: List[int]
    col_constraints_water: List[int]
    ship_constraints: List[int]
    board_size: int
    next_ship: List[List[Ship]]
    current_ship_size: int

    def __init__(self, board_size: int, row_constraints: List[int], col_constraints: List[int],
                 ship_constraints: List[int]):
        self.board_size = board_size
        self.board_representation = [["0" for _ in range(board_size)] for _ in range(board_size)]
        self.row_constraints = row_constraints
        self.row_constraints_water = [board_size - x for x in row_constraints]
        self.col_constraints = col_constraints
        self.col_constraints_water = [board_size - x for x in col_constraints]
        self.ship_constraints = [0, ] + ship_constraints
        self.next_ship = [[Ship(Location(x, y), i, v) for i in range(4, -1, -1) for v in [True, False]] for y in
                          range(board_size) for x in range(board_size)]

    # def get_next_ship(self) -> Optional[Ship]:
    #     if self.next_ship:
    #         return self.next_ship.pop()
    #
    #     if self.next_ship == None:
    #         self.current_ship_size = 4
    #     else:
    #         if self.ship_constraints[self.current_ship_size] > 0:
    #             raise ControlFlowError(
    #                 "Cannot place a ship of size {} when there are {} ships of that size left".format(
    #                     self.current_ship_size, self.ship_constraints[self.current_ship_size]))
    #         self.current_ship_size -= 1
    #     while self.current_ship_size > 0 and self.ship_constraints[self.current_ship_size] == 0:
    #         self.current_ship_size -= 1
    #     if self.current_ship_size == 0:
    #         return None
    #
    #     self.next_ship = []
    #     for y in range(self.board_size):
    #         for x in range(self.board_size):
    #             for vertical in [True, False]:
    #                 ship = Ship(Location(x, y), self.current_ship_size, vertical)
    #                 self.next_ship.append(ship)
    #     return self.get_next_ship()

    def on_board(self, Location: Location) -> bool:
        return 0 <= Location.x < self.board_size and 0 <= Location.y < self.board_size

    def __getitem__(self, item: Location) -> str:
        return self.board_representation[item.y][item.x]

    def __setitem__(self, key: Location, value: str):
        if value == ".":
            if not self.on_board(key):
                return
            item = self[key]
            if item != "0" and item != ".":
                raise ControlFlowError("Cannot place a dot on a non-empty cell")
            if item == "0":
                self.col_constraints_water[key.x] -= 1
                self.row_constraints_water[key.y] -= 1
                if self.col_constraints_water[key.x] < 0 or self.row_constraints_water[key.y] < 0:
                    raise ControlFlowError("too many dots in a row or column")
            self.board_representation[key.y][key.x] = value
        else:
            if not self.on_board(key):
                raise ControlFlowError("Cannot place a ship outside the board")

            item = self[key]
            if item != "0":
                raise ControlFlowError("cannot place a ship on a non-empty cell")

            self.board_representation[key.y][key.x] = value
            self.col_constraints[key.x] -= 1
            self.row_constraints[key.y] -= 1

            if self.col_constraints[key.x] < 0 or self.row_constraints[key.y] < 0:
                raise ControlFlowError("too many ships in a row or column")

    def place_ship(self, ship: Ship):
        if ship.size == 0:
            self[ship.start] = "."
            return
        ship_string = ship.ship_string()
        ship_location_offset = ship.start + Location(-1, -1)
        for y, row in enumerate(ship_string.splitlines()):
            for x, char in enumerate(row):
                self[ship_location_offset + Location(x, y)] = char
        self.ship_constraints[ship.size] -= 1
        if self.ship_constraints[ship.size] < 0:
            raise ControlFlowError("too many ships of size {}".format(ship.size))

    def __repr__(self):
        board = "\n".join("".join(row) for row in self.board_representation)

        return board

    def solve_hint(self, hint: str, hint_location: Location) -> List[Board]:
        if hint == "0":
            return [self]
        elif hint == ".":
            self[hint_location] = "."
            return [self]
        else:
            if self[hint_location] == hint:
                return [self]
            else:
                result = []
                for x in range(self.board_size):
                    for y in range(self.board_size):
                        for size in range(1, 5):
                            for vertical in [True, False]:
                                ship = Ship(Location(x, y), size, vertical)
                                try:
                                    new_board = copy.deepcopy(self)
                                    new_board.place_ship(ship)
                                    if new_board[hint_location] == hint:
                                        result.append(new_board)
                                except ControlFlowError as e:
                                    pass
                return result

    def backtracking(self) -> Board:
        while True:
            if not self.next_ship:
                return self
            ships = self.next_ship.pop()
            for ship in ships:
                try:
                    new_board = copy.deepcopy(self)
                    new_board.place_ship(ship)
                    return new_board.backtracking()
                except ControlFlowError as e:
                    pass
            raise ControlFlowError("No possible ship placements")

    def solve(self, board_str: List[List[str]]) -> Board:
        boards = self.solve_all_hints(board_str)
        for board in boards:
            backtracked_board = None
            try:
                backtracked_board = board.backtracking()
            except ControlFlowError as e:
                pass
            if backtracked_board is not None:
                return backtracked_board

    def solve_all_hints(self, board_str: List[List[str]]) -> List[Board]:
        result = [self]
        for y, row in enumerate(board_str):
            for x, hint in enumerate(row):
                result = [new_board for board in result for new_board in board.solve_hint(hint, Location(x, y))]
        return result


if __name__ == '__main__':
    file = open("input_easy1.txt", "r")
    board_str = file.read().splitlines()
    board_str = [list(row) for row in board_str]
    sizes = [int(x) for x in board_str[2]]
    row_constraints = [int(x) for x in board_str[0]]
    col_constraints = [int(x) for x in board_str[1]]
    size = len(board_str[0])
    board_str = board_str[3:]
    board = Board(size, row_constraints, col_constraints, sizes)
    time1 = time.time()
    print(board.solve(board_str))
    time2 = time.time()
    print(time2 - time1)
