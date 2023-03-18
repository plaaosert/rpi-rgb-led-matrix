import math


class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def check_type(other):
        if not isinstance(other, Vector2):
            raise TypeError("Other element must be Vector2")

    def floor_to_intvec(self):
        return Vector2(int(self.x), int(self.y))

    def __str__(self):
        return "{},{}".format(self.x, self.y)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.x, self.y))

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __add__(self, other):
        Vector2.check_type(other)

        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        Vector2.check_type(other)

        return self + (-other)

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        else:
            return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        else:
            return Vector2(self.x / other, self.y / other)

    def __floordiv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x // other.x, self.y // other.y)
        else:
            return Vector2(self.x // other, self.y // other)

    def __abs__(self):
        return Vector2(abs(self.x), abs(self.y))

    def magnitude(self):
        return math.sqrt((self.x ** 2) + (self.y ** 2))

    def distance(self, other):
        return abs(other - self).magnitude()

    def normalized(self):
        return self / self.magnitude()
