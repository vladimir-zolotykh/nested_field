import struct
import itertools

PolyType = list[tuple[float, float]]
PolysType = list[PolyType]
polys: PolysType = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 6.3), (1.2, 0.5), (4.6, 9.2)],
]

PointType = tuple[float, float]


def boundingbox(polys: PolysType) -> tuple[PointType, PointType]:
    # Determine bounding box
    flattened = list(itertools.chain(*polys))
    x1 = min(x for x, y in flattened)
    x2 = max(x for x, y in flattened)
    y1 = min(y for x, y in flattened)
    y2 = max(y for x, y in flattened)
    return (x1, y1), (x2, y2)


def write_polys(filename: str, polys: PolysType) -> None:
    bb = boundingbox(polys)
    min_x, min_y = bb[0]
    max_x, max_y = bb[1]

    with open(filename, "wb") as f:
        f.write(struct.pack("<iddddi", 0x1234, min_x, min_y, max_x, max_y, len(polys)))

        for poly in polys:
            size = len(poly) * struct.calcsize("<dd")
            f.write(struct.pack("<i", size + 4))
            for pt in poly:
                f.write(struct.pack("<dd", *pt))


# Call it with our polygon data
write_polys("polys.bin", polys)
