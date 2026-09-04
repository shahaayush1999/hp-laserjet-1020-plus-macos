"""Normal ZjStream START_PAGE low work fields (not the alternate copier)."""
# id, symbolic item name, destination byte offset, extra instruction before store
DIRECT_U16_FIELDS = [
    (3, 'ZJI_DMPAPER', 0x0a, 0), (4, 'ZJI_DMCOPIES', 0x0c, 0),
    (6, 'ZJI_DMMEDIATYPE', 0x10, 0), (7, 'ZJI_NBIE', 0x12, 0),
    (8, 'ZJI_RESOLUTION_X', 0x14, 3), (9, 'ZJI_RESOLUTION_Y', 0x16, 3),
    (10, 'ZJI_OFFSET_X', 0x18, 0), (11, 'ZJI_OFFSET_Y', 0x1c, 0),
    (12, 'ZJI_RASTER_X', 0x1e, 0), (13, 'ZJI_RASTER_Y', 0x20, 0),
    (16, 'ZJI_VIDEO_BPP', 0x22, 0), (17, 'ZJI_VIDEO_X', 0x24, 0),
    (18, 'ZJI_VIDEO_Y', 0x26, 0), (19, 'ZJI_INTERLACE', 0x2a, 0),
    (22, 'ZJI_RET', 0x30, 0), (23, 'ZJI_ECONOMODE', 0x32, 0),
]


def direct_work_fields(items):
    fields = {f'+0x{offset:02x}': int(items.get(name, 0)) & 0xffff
              for _, name, offset, _ in DIRECT_U16_FIELDS}
    fields['+0x0c'] = fields['+0x0c'] or 1
    fields.update({'+0x36': 0, '+0x74': 0})
    return fields
