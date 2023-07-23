from collections.abc import Sequence
from enum import Enum

__all__ = ('PaintType', 'Color', 'ColorMix', 'Paint', 'Decal')


class PaintType(Enum):
    """Enumeration type to distinguish ways to apply paint to model parts."""

    SPRAY = 1
    BRUSH = 2


class Color:
    """Color object specifies colors of model paints. While a single color code or name will usually suffice, the Color
    object allows for brand, code and name properties in order to avoid any ambiguities. The brand is required, however
    only one of code and name must be specified. While code can be anything (serial number, color code, etc.) it would
    make the most sense (and simplify user experience) to use whichever color coding is used by the model instructions.
    (Note: brand, code, and name are all string types, so even if color codes are numeric, Color objects must be
    constructed with string types.)

    Color objects are used to instantiate Paint objects (see Paint class). To simplify the interface, Color objects
    automatically create both types of Paint objects that can possibly be created (see PaintType enum) and are
    accessible via the 'spray' and 'brush' properties."""

    __slots__ = '_brand', '_name', '_code', '_spray', '_brush'

    def __init__(self, brand: str, code: str, name: str):
        if not isinstance(brand, str):
            raise TypeError(f'brand must be a str type, not {type(brand)}')
        if not isinstance(code, str):
            raise TypeError(f'code must be a str type, not {type(brand)}')
        if not isinstance(name, str):
            raise TypeError(f'name must be a str type, not {type(name)}')

        if not code and not name:
            raise ValueError('no handle specified; code and name cannot both be empty strings')

        self._brand = brand
        self._code = code
        self._name = name

        # Paint objects to return for spray and brush properties
        self._spray = Paint(self, PaintType.SPRAY)
        self._brush = Paint(self, PaintType.BRUSH)

    @property
    def brand(self):
        return self._brand

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def spray(self):
        return self._spray

    @property
    def brush(self):
        return self._brush

    def __str__(self):
        return f'<{self._brand}, {self._code}, {self._name}>'

    def __repr__(self):
        return f'{self.__class__.__name__}({self._brand}, {self._code}, {self._name})'

    def __hash__(self):
        return hash((self._brand, self._code, self._name))

    def __eq__(self, other: 'Color'):
        if isinstance(other, Color):
            return self.__hash__() == other.__hash__()
        return NotImplemented


class ColorMix(Color):
    """The ColorMix class enables a Color object to be created as a ratio of two or more Color objects. The resulting
    code is a concatenation of codes or names of the base Colors used in the color mixture. If the Color has a code
    property, it is used, otherwise the name property is used (Color objects are forced to have either a code or name).
    A name for the mixture color can be passed as an optional constructor argument.

    If all colors have the same brand, the ColorMix will have that brand, otherwise the brand property will be set
    to 'Mixture'."""

    def __init__(self, colors: list[tuple[Color, int]], name: str = ''):
        brand, code = self._checkArgs(colors)
        if brand is False:
            brand = 'Mixture'

        super().__init__(brand, code, name)

    @staticmethod
    def _checkArgs(colors: list[tuple[Color, int]]):
        if not isinstance(colors, Sequence):
            raise TypeError(f'colors must be a Sequence type, not {type(colors)}')

        handles = []
        brand = colors[0][0].brand
        for c in colors:
            if not isinstance(c, tuple):
                raise TypeError(f'each element of colors must be a tuple type, not {type(c)}')
            elif (l := len(c)) != 2:
                raise ValueError(f'each tuple of colors must have exactly two elements, not {l}')
            else:
                if not isinstance(c[0], Color):
                    raise TypeError(f'first element of each colors tuple must be a Color type, not {type(c[0])}')
                elif not isinstance(c[1], int):
                    raise TypeError(f'second element of each colors tuple must be an int type, not {type(c[1])}')

                if brand and c[0].brand != brand:
                    brand = False
                if c[0].code:
                    handle = f'{c[0].code}:{c[1]}'
                elif c[0].name:
                    handle = f'{c[0].name}:{c[1]}'
                else:
                    raise ValueError(f'color ({str(c[0])}) must have either a code or a name (it has neither)')
                handles.append(handle)

        code = ' + '.join(handles)

        return brand, code


class Paint:
    """The Paint object specifies how to paint a specific color. The only options for any color are spray, and brush
    (see PaintType enum). A Color object is necessary to instantiate a Paint object, and a Color object can return
    the necessary Paint object dependent on the desired PaintType. Therefore, while certainly possible to instantiate a
    Paint object yourself, it is never actually needed to."""

    __slots__ = '_color', '_type'

    def __init__(self, color: Color, paintType: PaintType):
        if not isinstance(color, Color):
            raise TypeError(f'color must be a Color type, not {type(color)}')
        if not isinstance(paintType, PaintType):
            raise TypeError(f'paintType must be a PaintType type, not {type(paintType)}')

        self._color = color
        self._type = paintType

    @property
    def color(self):
        return self._color

    @property
    def type(self):
        return self._type

    def __str__(self):
        return f'<{str(self._color)}, {self._type}>'

    def __repr__(self):
        return f'{self.__class__.__name__}({self._color}, {self._type})'

    def __hash__(self):
        return hash((self._color, self._type))

    def __eq__(self, other: 'Paint'):
        if isinstance(other, Paint):
            return self.__hash__() == other.__hash__()
        return NotImplemented


class Decal:
    """The Decal class is used ot represent a decal to be applied to a diecast part. A very simple object, the only
    component of the class is the identifier of the decal."""

    __slots__ = '_id'

    def __init__(self, id: str):
        if not isinstance(id, str):
            raise TypeError(f'id must be a str type, not {type(id)}')

        self._id = id

    @property
    def id(self):
        return self._id

    def __hash__(self):
        return hash((self.__class__.__name__, self._id))

    def __eq__(self, other: 'Decal'):
        if isinstance(other, Decal):
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __str__(self):
        return f'<decal {self._id}>'

    def __repr__(self):
        return f'{self.__class__.__name__}({self._id})'
