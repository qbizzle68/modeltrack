from collections.abc import Sequence
from copy import deepcopy, copy
from pickle import dump, load

from .detail import Color, Paint, Decal


class HashMap(dict):
    """A custom map type that is hashable. The hash is based upon sorting the keys by their own hash values with the
    class name as a kind of salt. This means every key must be hashable, and the values of the mapping play no role in
    the hash value."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        """Convert the keys to a sorted tuple, relying on the hash of the key's themselves to determine the order.
        Sorting the keys ensures insertion order of the map does not affect the hash value."""

        return hash((self.__class__.__name__,) + tuple(sorted(self.keys(), key=lambda o: hash(o))))


class PaintMap(HashMap):
    """A custom hashable map type meant to map Paint types to boolean values. It is very easy to accidentally use a
    Color type instead of a Paint type to set a key's value. This of course, results in adding a new key value pair to
    the map. This custom class raises a TypeError when trying to use a Color object as a key."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        """Raising an exception if key is not in the map does not allow the object to be copied with the copy module, so
        we just strictly enforce the key cannot be a Color type (this is the entire point of defining this class
        anyway). We also type check the value while we are here as well."""

        if type(key) == Color:
            raise TypeError('Color object used where Paint object was expected.')
        elif value not in (True, False, None):
            raise TypeError(f'value must be True, False, or None, not {value}')

        dict.__setitem__(self, key, value)


def _checkString(value, name):
    if not isinstance(value, str):
        raise TypeError(f'{name} must be a str type, not {type(value)}')


class Part:
    __slots__ = '_id', '_paints', '_decals', '_master'

    def __init__(self, id: str, paints: list[Paint] = None, decals: list[Decal] = None):
        _checkString(id, 'id')
        self._id = id

        if paints is None:
            self._paints = PaintMap()
        elif isinstance(paints, Paint):
            self._paints = PaintMap({paints: False})
        elif isinstance(paints, Sequence):
            for p in paints:
                if not isinstance(p, Paint):
                    raise TypeError(f'every element of paints must be a Paint type, not {type(p)}')
            self._paints = PaintMap(zip(paints, (False,) * len(paints)))
        else:
            raise TypeError(f'paints must be a Paint instance or a sequence of Paint instances or None, not '
                            f'{type(paints)}')

        if decals is None:
            self._decals = HashMap()
        elif isinstance(decals, Decal):
            self._decals = HashMap({decals: False})
        elif isinstance(decals, Sequence):
            for d in decals:
                if not isinstance(d, Decal):
                    raise TypeError(f'every element of decals must be a Decal type, not {type(d)}')
            self._decals = HashMap(zip(decals, (False,) * len(decals)))
        else:
            raise TypeError(f'decals must be a Decal instance or a sequence of Decal instances or None, not '
                            f'{type(decals)}')

        self._master = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def paints(self) -> PaintMap[Paint]:
        return self._paints

    @property
    def decals(self) -> PaintMap[Decal]:
        return self._decals

    @property
    def master(self) -> 'Step':
        return self._master

    @master.setter
    def master(self, value: 'Step'):
        if not isinstance(value, Step):
            raise TypeError(f'value must be a Step type, not {type(value)}')

        if self._master is None:
            self._master = value
        else:
            raise ValueError(f'master value already set')

    def checkPaint(self, paint: Paint) -> bool | None:
        """Returns the boolean value for the painted status of paint on this Part. If paint is not in Part.paints, None
        is returned."""

        if not isinstance(paint, Paint):
            raise TypeError(f'paint must be a Paint type, not {type(paint)}')

        return self._paints.get(paint)

    def checkDecal(self, decal: Decal) -> bool | None:
        """Returns the boolean value for the decaled status of decal on this part. If decal is not in Part.decals, None
        is returned."""

        if not isinstance(decal, Decal):
            raise TypeError(f'decal must be a Decal type, not {type(decal)}')

        return self._decals.get(decal)

    def isPainted(self) -> bool:
        """Returns True if the Part is fully painted, False otherwise."""

        for v in self._paints.values():
            if v is False:
                return False
        return True

    def isDecaled(self) -> bool:
        """Returns True if the Part is fully decaled, False otherwise."""

        for v in self._decals.values():
            if v is False:
                return False
        return True

    def isComplete(self) -> bool:
        """Returns True if the Part is fully painted and decaled, False otherwise."""

        return self.isPainted() and self.isDecaled()

    def copy(self, number: int = 1) -> 'Part' | tuple['Part']:
        """Returns a single or a number of copies of a Part.

        Raises TypeError if number is not an int and a ValueError if number <= 0."""

        if not isinstance(number, int):
            raise TypeError(f'number must be an int type, not {type(number)}')
        if number <= 0:
            raise ValueError(f'number must be a positive number, (number = {number})')
        elif number > 1:
            return (deepcopy(self) for _ in range(number))
        else:
            return deepcopy(self)

    def __hash__(self):
        return hash((self._id, self._paints, self._decals))

    def __eq__(self, other: 'Part'):
        if type(other) == Part:
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __str__(self):
        paintStrings = [f'{str(k)}: {v}' for k, v in self._paints.items()]
        paintStr = ', '.join(paintStrings)

        decalStrings = [f'{str(k)}: {v}' for k, v in self._decals.items()]
        decalStr = ', '.join(decalStrings)

        return f'\'{self._id}\', {{{paintStr}}}, {{{decalStr}}}'

    def __repr__(self):
        return f'Part({repr(self._id)}, {repr(self._paints)}, {repr(self._decals)})'

    def __contains__(self, item: Paint | Decal):
        if isinstance(item, Paint):
            return item in self._paints
        elif isinstance(item, Decal):
            return item in self._decals
        else:
            raise TypeError(f'item must be a Paint or Decal type, not {type(item)}')


class Assembly(Part):
    __slots__ = '_parts', '_assemblies'

    def __init__(self, id: str, parts: 'list[Part | Assembly] | Part | Assembly'):
        # We assume all Parts/Assemblies are already 'attached' to their Step when we're creating new Parts/Assemblies,
        # so all new Parts/Assemblies will have a master of None, so master equality still works.
        self._master = None

        if type(parts) == Part or type(parts) == Assembly:
            parts = (parts,)

        if isinstance(parts, Sequence):
            partList, assemblies, paints, decals = self._parseParts(parts)

            self._parts = partList
            self._assemblies = assemblies

            super().__init__(id, tuple(paints), tuple(decals))
        else:
            raise TypeError(f'parts must be a Sequence type, not {type(parts)}')

    @staticmethod
    def _parseParts(parts: list['Part | Assembly']) -> (list['Part | Assembly'], list['Assembly'], tuple[Paint],
                                                        tuple[Decal]):
        paints = set()
        decals = set()
        partList = []
        assemblies = []

        for p in parts:
            if type(p) == Part:
                partList.append(p)
            elif type(p) == Assembly:
                # We don't copy assemblies here because we expect an assembly that is part of a larger assembly will
                # not be 'expanded' to another assembly (using the .attach() method), thus we don't need to force
                # ambiguities (in memory addresses) for those assemblies.
                partList.append(p)
                assemblies.append(p)
            else:
                raise TypeError(f'every element of parts must be a Part or Assembly type, not {type(p)}')

            paints |= set(p.paints.keys())
            decals |= set(p.decals.keys())

        return partList, assemblies, paints, decals

    @property
    def parts(self):
        return self._parts

    @property
    def assemblies(self):
        return self._assemblies

    def isPainted(self) -> bool:
        for p in self._parts:
            if p.isPainted() is False:
                return False

        return True

    def isDecaled(self) -> bool:
        for p in self._parts:
            if p.isDecaled() is False:
                return False

        return True

    def get(self, part: 'str | Part | Assembly', recursive=False):
        """Searches for all instances of part in the same step as the Assembly. If recursive is True, all subassemblies
        are recursively searched for the part as well.

        part can be either a Part or Assembly type, or a str type whose value is matched against the part's id property.
        """

        if isinstance(part, str):
            rtn = [p for p in self._parts if p.id == part]

            for a in self._assemblies:
                if a._master is self._master:
                    rtn += a.get(part, recursive=recursive)
                elif recursive is True:
                    rtn += a.get(part, recursive=True)

            # if recursive is True:
            #     for a in self._assemblies:
            #         if a.master is self.master:
            #             rtn += a.get(part, True)

            return rtn
        elif isinstance(part, Part):
            rtn = [p for p in self._parts if p == part]

            for a in self._assemblies:
                if a._master is self._master:
                    rtn += a.get(part, recursive=recursive)
                elif recursive is True:
                    rtn += a.get(part, recursive=True)

            # if recursive is True:
            #     for a in self._assemblies:
            #         if a.master is self.master:
            #             rtn += a.get(part, True)

            return rtn
        else:
            raise TypeError(f'part must be a str, Part, or Assembly type, not {type(part)}')

    def attach(self, parts: 'list[Part | Assembly] | Part | Assembly'):
        """Add a list of Parts or Assemblies to an existing Assembly. The existing master property will be set to None.
        """

        # Any 'old' versions of the Assembly are copied into their Steps, so this master should be reset.
        self._master = None

        if type(parts) == Part or type(parts) == Assembly:
            parts = (parts,)

        if isinstance(parts, Sequence):
            partList, assemblies, paints, decals = self._parseParts(parts)

            self._parts = copy(self._parts) + partList
            self._assemblies = copy(self._assemblies) + assemblies

            for p in paints:
                if p not in self._paints:
                    self._paints.update({p: False})
            for d in decals:
                if d not in self._decals:
                    self._decals.update({d: False})
        else:
            raise TypeError(f'parts must be a Sequence type, not {type(parts)}')

    @Part.master.setter
    def master(self, value: 'Step'):
        if not isinstance(value, Step):
            raise TypeError(f'value must be a Step type, not {type(value)}')

        # Track if any value was set, raising an exception if not, as that indicative of an error (there should
        # always be an item to set master if this is being called).
        changed = False
        if self._master is None:
            self._master = value
            changed = True

        for p in self._parts:
            if p._master is None:
                p.master = value
                if changed is False:
                    changed = True
            # else:
            #     try:
            #         p.master = value
            #         changed = True
            #     except:
            #         pass

        if changed is False:
            raise ValueError(f'master values already set')

    def getUnpainted(self, paint: Paint = None, recursive=False) -> list[Part]:
        if paint is not None and not isinstance(paint, Paint):
            raise TypeError(f'paint must be a Paint type, not {type(paint)}')
        if not isinstance(recursive, bool):
            raise TypeError(f'recursive must be a bool type, not {type(recursive)}')

        unpainted = []
        for p in self._parts:
            if p.paints.get(paint) is False:
                unpainted.append(p)

        for a in self._assemblies:
            unpainted += a.getUnpainted(paint, recursive)

        return unpainted

    def getUndecaled(self, recursive=False) -> list[Decal]:
        if not isinstance(recursive, bool):
            raise TypeError(f'recursive must be a bool type, not {type(recursive)}')

        undecaled = [p for p in self._parts if p.isDecaled() is False]
        if recursive is True:
            for a in self._assemblies:
                undecaled.append(a)

        return undecaled

    def __hash__(self):
        return hash((super().__hash__(), tuple(self._parts)))

    def __eq__(self, other: 'Assembly'):
        if isinstance(other, Assembly):
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __str__(self):
        lines = [f'[{str(p)}]' for p in self._parts]
        parts = '\n'.join(lines)
        return f'\'{self._id}\' :\n{parts}'

    def __repr__(self):
        return f'Assembly({self._id}, {self._parts})'

    def __contains__(self, item: 'Part | Assembly'):
        if type(item) != Part and type(item) != Assembly:
            raise TypeError(f'item must be a Part or Assembly type, not {type(item)}')

        parts = self.get(item, recursive=False)
        if parts:
            return True
        return False


class Step(Assembly):
    __slots__ = '_previous'

    def __init__(self, name: str, parts: list[Part | Assembly] | Part | Assembly, previous: 'Step'):
        if previous is not None and not isinstance(previous, Step):
            raise TypeError(f'previous must be None or a Step type, not {type(previous)}')
        self._previous = previous

        if type(parts) == Part:
            parts.master = self
            partsArg = (parts,)
        elif type(parts) == Assembly:
            parts.master = self
            partsArg = (copy(parts),)
        else:
            tmp = []
            for p in parts:
                if type(p) == Part:
                    tmp.append(p)
                elif type(p) == Assembly:
                    tmp.append(copy(p))
                else:
                    raise TypeError(f'all elements of parts must be an Assembly or Part type, not {type(p)}')
                p.master = self
            partsArg = tuple(tmp)

        super().__init__(name, partsArg)

    @property
    def previous(self):
        return self._previous

    def __hash__(self):
        return hash((self.__class__.__name__, super().__hash__()))

    def __eq__(self, other: 'Step'):
        if isinstance(other, Step):
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __str__(self):
        partString = super().__str__().lstrip(f"'{self._id}' :\n")
        return f'Step {self._id}:\n{partString}'

    def __repr__(self):
        return f'Step({self._id}, {self._parts}, {self._previous})'


class Model:
    __slots__ = '_name', '_steps', '_parts', '_assemblies', '_paints', '_decals'

    def __init__(self, name: str):
        _checkString(name, 'name')
        self._name = name

        self._steps = []
        self._parts = {}
        self._assemblies = {}
        self._paints = {}
        self._decals = {}

    def nextStep(self, name: str, parts: list[Part | Assembly] | Part | Assembly):
        previous = self._steps[-1] if self._steps else None
        step = Step(name, parts, previous=previous)
        self._steps.append(step)

        for part in step.parts:
            if part not in self._parts:
                self._parts[part.id] = part
        for assembly in step.assemblies:
            if assembly not in self._assemblies:
                self._assemblies[assembly.id] = assembly
        for paint in step.paints:
            if paint not in self._paints:
                if paint.color.code:
                    key = (paint.color.code, paint.type)
                else:
                    key = (paint.color.name, paint.type)
                self._paints[key] = paint
        for decal in step.decals:
            if decal not in self._decals:
                self._decals[decal.id] = decal

    def getStep(self, number: int | str) -> Step:
        """Return the step by either a number or name. If number is an int, returns the step where number is the
        absolute step number, not an index. If number is a string, return the first step whose name matches the string,
        raising a ValueError if none are found."""
        if isinstance(number, int):
            return self._steps[number - 1]
        elif isinstance(number, str):
            for s in self._steps:
                if s.id == number:
                    return s
            raise ValueError(f'no step name matches {number}')
        else:
            raise TypeError(f'number must be an int or str type, not {type(number)}')

    def save(self, filename=None):
        if filename is None:
            filename = self._name

        with open(filename, 'wb') as f:
            dump(self, f)

    @property
    def name(self):
        return self._name

    @property
    def parts(self):
        return self._parts

    @property
    def assemblies(self):
        return self._assemblies

    @property
    def paints(self):
        return self._paints

    @property
    def decals(self):
        return self._decals

    def __len__(self):
        return len(self._steps)

    def __getitem__(self, item: int):
        return self._steps[item]


def loadModel(filename: str) -> Model:
    """Load a saved model file from filename."""

    if not isinstance(filename, str):
        raise TypeError(f'filename must be a str type, not {type(filename)}')

    with open(filename, 'rb') as f:
        model = load(f)

    if not isinstance(model, Model):
        raise TypeError(f'object pickled at {filename} is not a {Model.__class__} type')

    return model
