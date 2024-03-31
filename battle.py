from __future__ import annotations

import argparse
import copy
import time
from dataclasses import dataclass
from typing import *
from enum import Enum


class Direction:
    x: int
    y: int
    vertical: Optional[bool] = None

    def __init__(self, x: int, y: int, vertical: Optional[bool] = None):
        self.x = x
        self.y = y
        self.vertical = vertical

    def __add__(self, other: Direction) -> Direction:
        return Direction(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> Direction:
        return Direction(self.x * other, self.y * other)


@dataclass
class Ship:
    size: int
    first_piece: Direction
    vertical: bool

    def rectangle(self) -> Tuple[Direction, Direction]:
        upper_left = self.first_piece + Direction(-1, -1)
        if self.vertical:
            bottom_right = self.first_piece + Direction(1, self.size)
        else:
            bottom_right = self.first_piece + Direction(self.size, 1)
        return upper_left, bottom_right

    def actual_box(self) -> Tuple[Direction, Direction]:
        top = self.first_piece
        if self.vertical:
            bottom = self.first_piece + Direction(0, self.size - 1)
        else:
            bottom = self.first_piece + Direction(self.size - 1, 0)
        return top, bottom

    def find_rect_overlap(self, is_vertical: bool, size: int) -> Tuple[Direction, Direction]:
        upper_left, bottom_right = self.rectangle()
        if self.size == 0:
            bottom_right = self.first_piece
        size_adjustment = size - 1
        if is_vertical:
            upper_left = upper_left + Direction(0, -size_adjustment)
        else:
            upper_left = upper_left + Direction(-size_adjustment, 0)

        return upper_left, bottom_right


class ShipException(Exception):
    pass


class Domain:
    domain_size: int
    num_ships_remaining: int
    ship_size: int
    vertical_ships: List[List[bool]]
    horizontal_ships: List[List[bool]]
    board_size: int

    def __init__(self, board_size: int, ship_size: int, num_ships: int):
        self.ship_size = ship_size
        self.vertical_ships = [[True for _ in range(board_size)] for _ in range(board_size)]
        self.horizontal_ships = [[True for _ in range(board_size)] for _ in range(board_size)]
        self.board_size = board_size
        self.domain_size = board_size * board_size * 2
        self.num_ships_remaining = num_ships
        for x in range(board_size):
            for y in range(board_size):
                location = Direction(x, y)
                vertical_ship = Ship(ship_size, location, True)
                horizontal_ship = Ship(ship_size, location, False)
                actual_box_top, actual_box_bottom = vertical_ship.actual_box()
                if actual_box_bottom.x >= board_size or actual_box_bottom.y >= board_size:
                    direction = Direction(x, y, True)
                    self[direction] = False
                actual_box_top, actual_box_bottom = horizontal_ship.actual_box()
                if actual_box_bottom.x >= board_size or actual_box_bottom.y >= board_size:
                    direction = Direction(x, y, False)
                    self[direction] = False

    def __getitem__(self, key: Direction):
        if 0 <= key.x < self.board_size and 0 <= key.y < self.board_size:
            if key.vertical:
                return self.vertical_ships[key.y][key.x]
            else:
                return self.horizontal_ships[key.y][key.x]

    def __setitem__(self, key: Direction, value):
        if 0 <= key.x < self.board_size and 0 <= key.y < self.board_size:
            if value == False and self[key]:
                self.domain_size -= 1
                if key.vertical:
                    self.vertical_ships[key.y][key.x] = False
                else:
                    self.horizontal_ships[key.y][key.x] = False

    def domain(self) -> Generator[Ship]:
        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.vertical_ships[y][x]:
                    yield Ship(self.ship_size, Direction(x, y, True), True)
                if self.horizontal_ships[y][x]:
                    yield Ship(self.ship_size, Direction(x, y, False), False)

    def set_ship(self, ship: Ship):
        if self.num_ships_remaining == 0:
            return
        if ship.size == self.ship_size:
            self.num_ships_remaining -= 1
        upper_left, bottom_right = ship.find_rect_overlap(True, self.ship_size)

        for x in range(upper_left.x, bottom_right.x + 1):
            for y in range(upper_left.y, bottom_right.y + 1):
                direction = Direction(x, y, True)
                self[direction] = False

        upper_left, bottom_right = ship.find_rect_overlap(False, self.ship_size)
        for x in range(upper_left.x, bottom_right.x + 1):
            for y in range(upper_left.y, bottom_right.y + 1):
                direction = Direction(x, y, False)
                self[direction] = False

        if self.domain_size == 0 and self.num_ships_remaining > 0:
            raise ShipException("No more possible ship locations")
        elif self.domain_size < 0:
            raise Exception("Domain size is negative")

    def set_water(self, location: Direction):
        for x in range(location.x - self.ship_size + 1, location.x + 1):
            self[Direction(x, location.y, False)] = False
        for y in range(location.y - self.ship_size + 1, location.y + 1):
            self[Direction(location.x, y, True)] = False

        if self.domain_size == 0 and self.num_ships_remaining > 0:
            raise ShipException("No more possible ship locations")

        elif self.domain_size < 0:
            raise Exception("Domain size is negative")

    def __repr__(self):
        vertical_ships = [["V" if item else "." for item in row] for row in self.vertical_ships]
        horizontal_ships = [["H" if item else "." for item in row] for row in self.horizontal_ships]
        return "\n".join([" ".join(row) for row in vertical_ships]) + "\n\n" + "\n".join(
            [" ".join(row) for row in horizontal_ships])

    def remaining_ship_row(self, row: int, remaining_ship: int):
        if remaining_ship == 0:
            for x in range(self.board_size):
                self.set_water(Direction(x, row, False))

        elif remaining_ship < self.ship_size:
            for x in range(self.board_size):
                self[Direction(x, row, False)] = False

    def remaining_ship_col(self, col: int, remaining_ship: int):
        if remaining_ship == 0:
            for y in range(self.board_size):
                self.set_water(Direction(col, y, True))
        elif remaining_ship < self.ship_size:
            for y in range(self.board_size):
                self[Direction(col, y, True)] = False


class Board:
    ships: List[Ship]
    size: int
    submarine_domain: Domain
    two_ship_domain: Domain
    three_ship_domain: Domain
    four_ship_domain: Domain
    domains: List[Domain]
    row_constraints: List[int]
    col_constraints: List[int]

    def board_repr(self) -> List[List[str]]:
        board = [["." for _ in range(self.size)] for _ in range(self.size)]
        for ship in self.ships:
            if ship.vertical:
                direction = Direction(0, 1)
            else:
                direction = Direction(1, 0)
            if ship.size == 1:
                board[ship.first_piece.y][ship.first_piece.x] = "S"
            elif ship.vertical:
                if ship.size == 2:
                    board[ship.first_piece.y][ship.first_piece.x] = "^"
                    board[ship.first_piece.y + 1][ship.first_piece.x] = "v"
                elif ship.size == 3:
                    board[ship.first_piece.y][ship.first_piece.x] = "^"
                    board[ship.first_piece.y + 1][ship.first_piece.x] = "M"
                    board[ship.first_piece.y + 2][ship.first_piece.x] = "v"
                elif ship.size == 4:
                    board[ship.first_piece.y][ship.first_piece.x] = "^"
                    board[ship.first_piece.y + 1][ship.first_piece.x] = "M"
                    board[ship.first_piece.y + 2][ship.first_piece.x] = "M"
                    board[ship.first_piece.y + 3][ship.first_piece.x] = "v"
            else:
                if ship.size == 2:
                    board[ship.first_piece.y][ship.first_piece.x] = "<"
                    board[ship.first_piece.y][ship.first_piece.x + 1] = ">"
                elif ship.size == 3:
                    board[ship.first_piece.y][ship.first_piece.x] = "<"
                    board[ship.first_piece.y][ship.first_piece.x + 1] = "M"
                    board[ship.first_piece.y][ship.first_piece.x + 2] = ">"
                elif ship.size == 4:
                    board[ship.first_piece.y][ship.first_piece.x] = "<"
                    board[ship.first_piece.y][ship.first_piece.x + 1] = "M"
                    board[ship.first_piece.y][ship.first_piece.x + 2] = "M"
                    board[ship.first_piece.y][ship.first_piece.x + 3] = ">"


        return board

    def __repr__(self):
        return "\n".join(["".join(row) for row in self.board_repr()])

    def __init__(self, size: int, ship_constraints: List[int] = None, row_constraints: List[int] = None,
                 col_constraints: List[int] = None):
        self.size = size
        if ship_constraints:
            self.submarine_domain = Domain(size, 1, ship_constraints[0])
            self.two_ship_domain = Domain(size, 2, ship_constraints[1])
            self.three_ship_domain = Domain(size, 3, ship_constraints[2])
            self.four_ship_domain = Domain(size, 4, ship_constraints[3])
            self.domains = [self.submarine_domain, self.two_ship_domain, self.three_ship_domain, self.four_ship_domain]
            self.row_constraints = row_constraints
            self.col_constraints = col_constraints
            self.ships = []
            for row in range(size):
                for domain in self.domains:
                    domain.remaining_ship_row(row, row_constraints[row])
            for col in range(size):
                for domain in self.domains:
                    domain.remaining_ship_col(col, col_constraints[col])


    def set_ship(self, ship: Ship):
        direction = ship.first_piece
        vertical = ship.vertical
        size = ship.size
        self.ships.append(ship)
        for domain in self.domains:
            domain.set_ship(ship)

        if vertical:
            for y in range(direction.y, direction.y + size):
                self.row_constraints[y] -= 1
                if self.row_constraints[y] < 0:
                    raise ShipException("Ship does not fit in board")
            self.col_constraints[direction.x] -= size
        else:
            self.row_constraints[direction.y] -= size
            for x in range(direction.x, direction.x + size):
                self.col_constraints[x] -= 1
                if self.col_constraints[x] < 0:
                    raise ShipException("Ship does not fit in board")

        if self.row_constraints[direction.y] < 0 or self.col_constraints[direction.x] < 0:
            raise ShipException("Ship does not fit in board")

        for domain in self.domains:
            domain.remaining_ship_row(direction.y, self.row_constraints[direction.y])
            domain.remaining_ship_col(direction.x, self.col_constraints[direction.x])

        self.domains = [domain for domain in self.domains if domain.num_ships_remaining > 0]

    def handle_simple_hints(self, board_str: List[List[str]]):
        for row in range(self.size):
            for col in range(self.size):
                hint = board_str[row][col]
                if hint == "S":
                    self.set_ship(Ship(1, Direction(col, row), False))
                elif hint == ".":
                    for domain in self.domains:
                        domain.set_water(Direction(col, row, False))
    def handle_complex_hints(self, board_str: List[List[str]]) -> List[Board]:
        queue = [self]
        for row in range(self.size):
            for col in range(self.size):
                hint = board_str[row][col]
                if hint in ["^", "v", "<", ">", "M"]:
                    new_queue = []
                    for board in queue:
                        if board.validate_hint(Direction(col, row), hint):
                            new_queue.append(board)
                        else:
                            new_queue += board.find_hint(Direction(col, row), hint)
                    queue = new_queue
        return queue



    def find_hint(self, location: Direction, hint: str) -> List[Board]:
        new_boards = []
        for domain in self.domains:
            for value in domain.domain():
                new_board = copy.deepcopy(self)
                try:
                    new_board.set_ship(value)
                    if new_board.board_repr()[location.y][location.x] == hint:
                        new_boards.append(new_board)
                except:
                    pass
        return new_boards

    def validate_hint(self, location: Direction, hint: str) -> bool:
        if self.board_repr()[location.y][location.x] == hint:
            return True

    def backtracking(self) -> Optional[Board]:
        domains = sorted(self.domains, key=lambda x: x.domain_size)
        if len(domains) == 0:
            return self
        domain = domains[0]
        for move in domain.domain():
            domain[move.first_piece] = False

            new_board = copy.deepcopy(self)
            try:
                new_board.set_ship(move)
                result = new_board.backtracking()
                if result:
                    return result
            except:
                pass
    def solve(self, board_str):
        self.handle_simple_hints(board_str)
        boards = self.handle_complex_hints(board_str)
        for board in boards:
            result = board.backtracking()
            if result:
                return result











if __name__ == "__main__":
    # domain = Domain(10, 1, 1)
    # ship = Ship(2, Direction(3, 3), True)
    # domain.set_ship(ship)
    # domain.set_water(Direction(3, 9, False))
    # print(domain)
    # print(domain.domain_size)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()
    file = open(args.inputfile, 'r')

    board_str = file.read().splitlines()
    board_str = [list(row) for row in board_str]
    sizes = [int(x) for x in board_str[2]]
    row_constraints = [int(x) for x in board_str[0]]
    col_constraints = [int(x) for x in board_str[1]]
    size = len(board_str[0])
    board_str = board_str[3:]
    board = Board(size, sizes, row_constraints, col_constraints)
    final = board.solve(board_str)
    write_file = open(args.outputfile, 'w')
    write_file.write(final.__repr__())
    print(final)



    # print(board.four_ship_domain.num_ships_remaining)
