"""Declared metadata boundary used by stock's split-buffer parser."""
import struct

def metadata_bounds(payload,item_count,reserved):
    pos=0;violations=[];items=[]
    if reserved>len(payload):
        return dict(status='invalid',reserved=reserved,payload_bytes=len(payload),items=[],violations=['reserved exceeds payload'])
    for i in range(item_count):
        if pos+8>len(payload):violations.append(f'item {i} header exceeds payload');break
        size,ident=struct.unpack_from('>IH',payload,pos)
        if size<8 or pos+size>len(payload):violations.append(f'item {i} size exceeds payload or is too small');break
        bounded=pos+size<=reserved
        items.append(dict(index=i,id=ident,offset=pos,size=size,within_reserved=bounded))
        if not bounded:violations.append(f'item {i} id {ident:#x} occupies [{pos},{pos+size}) beyond declared metadata {reserved}')
        pos+=size
    return dict(status='bounded' if not violations else 'invalid',reserved=reserved,payload_bytes=len(payload),
                item_bytes=pos,items=items,violations=violations)
