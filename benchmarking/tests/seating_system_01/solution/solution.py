class Layout:

    """
    >>> layout = Layout('layout.txt')
    >>> print(layout)
    L.LL.LL.LL
    LLLLLLL.LL
    L.L.L..L..
    LLLL.LL.LL
    L.LL.LL.LL
    L.LLLLL.LL
    ..L.L.....
    LLLLLLLLLL
    L.LLLLLL.L
    L.LLLLL.LL
    >>> layout.occupied_seats()
    0
    >>> print(next(layout))
    #.##.##.##
    #######.##
    #.#.#..#..
    ####.##.##
    #.##.##.##
    #.#####.##
    ..#.#.....
    ##########
    #.######.#
    #.#####.##
    >>> layout.occupied_seats()
    71
    >>> print(next(layout))
    #.LL.L#.##
    #LLLLLL.L#
    L.L.L..L..
    #LLL.LL.L#
    #.LL.LL.LL
    #.LLLL#.##
    ..L.L.....
    #LLLLLLLL#
    #.LLLLLL.L
    #.#LLLL.##
    >>> layout.occupied_seats()
    20
    """

    def __init__(self, filename):

        with open(filename) as layout:
            self.grid = [list(row.rstrip('\n')) for row in layout]

        # determine the number of rows and cols of the grid
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

    def __str__(self):

        return '\n'.join(''.join(row) for row in self.grid)

    def neighbours(self, r, c):

        # determine eight possible directions
        directions = [
            (dr, dc)
            for dr in range(-1, 2)
            for dc in range(-1, 2)
            if (dr, dc) != (0, 0)
        ]

        # determine immediate neighbours
        neighbours = {}
        for dr, dc in directions:
            if 0 <= r + dr < self.rows and 0 <= c + dc < self.cols:
                seat = self.grid[r + dr][c + dc]
                neighbours[seat] = neighbours.get(seat, 0) + 1

        return neighbours

    def __iter__(self):
        return self

    def __next__(self):

        def next_state(row, col):
            if self.grid[row][col] == 'L' and self.neighbours(row, col).get('#', 0) == 0:
                return '#'
            elif self.grid[row][col] == '#' and self.neighbours(row, col).get('#', 0) >= 4:
                return 'L'
            else:
                return self.grid[row][col]

        # initialize new grid
        new_grid = [
            [next_state(row, col) for col in range(self.cols)]
            for row in range(self.rows)
        ]

        if new_grid == self.grid:
            raise StopIteration()

        self.grid = new_grid

        return self

    def occupied_seats(self):

        return sum(row.count('#') for row in self.grid)

def occupied_seats(filename):

    """
    >>> occupied_seats('layout.txt')
    37
    >>> occupied_seats('adventofcode.input.txt')
    2483
    """

    layout = Layout(filename)
    for layout in layout:
        pass

    return layout.occupied_seats()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
