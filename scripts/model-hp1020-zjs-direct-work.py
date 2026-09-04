#!/usr/bin/env python3
"""Verify the missing direct START_PAGE-to-work builder path against stock bytes."""
import hashlib
import json
from pathlib import Path
import runpy
import struct
from hp1020_work_fields import DIRECT_U16_FIELDS, direct_work_fields

ROOT = Path(__file__).resolve().parents[1]
read = runpy.run_path(str(ROOT/'scripts/recover-hp1020-division-decode.py'))['elf_range']

def word(address):
    return struct.unpack('>I', read(address, 4))[0]

def main():
    checks=[]
    def verify(name, address, expected, meaning):
        actual=read(address, len(bytes.fromhex(expected))).hex()
        checks.append(dict(name=name,address=f'0x{address:08x}',bytes=actual,
                           expected=expected,meaning=meaning,status='present' if actual==expected else 'missing'))
    table=word(0x1000600c)
    verify('chunk_switch_base',0x1000600c,'100036f0','chunk-type switch table')
    verify('start_page_target',table+2*4,'10009f86','ZjStream type 2 selects this handler')
    verify('work_allocate',0x10009faf,'58149e','call8 0x1000f228; returns 0x94 work in a10')
    verify('save_work',0x10009fb5,'d7a0','mov.n a7,a10')
    verify('builder_destination',0x10009fe0,'da702e7477','mov.n a10,a7; only writes flag byte +0x77')
    verify('builder_arguments',0x10009fe5,'2b12652c1267dd305bfed7',
           'a11=item buffer, a12=reserved length, a13=item count; call8 0x10009b4c')
    verify('work_queue_message',0x10009ffd,'c08598109713','queue message 5, payload a7 at stack+12')
    verify('builder_preserves_destination',0x10009b4f,'d720','mov.n a7,a2 saves incoming call8 destination')
    verify('builder_destination_for_stores',0x10009b67,'d270','mov.n a2,a7 restores destination before item dispatch')
    verify('default_copies',0x10009ff3,'287106cc83c0f12f7506','zero copies become one')
    item_table=word(0x10005ff8)
    fields=[]
    for item,name,offset,extra in DIRECT_U16_FIELDS:
        target=word(item_table+item*4)
        verify(f'{name}_load',target,'283105','l16ui a8,a3,10 takes low half of BE uint32 item')
        verify(f'{name}_store',target+3+extra,f'2825{offset//2:02x}',f's16i a8,a2,{offset}')
        fields.append(dict(item_id=f'0x{item:02x}',item=name,work_offset=f'+0x{offset:02x}',
                           switch_target=f'0x{target:08x}',width=16,default=1 if item==4 else 0))
    # Common initializer and allocation evidence are separately saved decompilations.
    init=(ROOT/'analysis/video-work-object/decompiled/1000f204_hp1020_work_common_init_candidate.c').read_text()
    create=(ROOT/'analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c').read_text()
    checks.append(dict(name='early_fields_zero_initialized',status='present' if 'FUN_1001b4c8(param_1,0,0x46)' in init and '0x94' in create else 'missing',meaning='common init zeros low body; missing RET defaults zero'))
    cases=[]
    for path in sorted((ROOT/'analysis/open-firmware-model/variants').glob('*/print-path-model.json')):
        model=json.loads(path.read_text()); items=model['objects']['pages'][0]['zjs_items']
        cases.append(dict(case=path.parent.name,fields=direct_work_fields(items)))
    report=dict(status='pass' if all(c['status']=='present' for c in checks) else 'fail',
                source_elf_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
                checks=checks,fields=fields,case_matrix=cases,
                conclusion='START_PAGE calls the item builder directly on the allocated 0x94 work; no hidden copy or alias is required.',
                correction=['+0x26 is VIDEO_Y; +0x30 is RET (absent => zero); +0x32 is ECONOMODE.',
                            '+0x22 is VIDEO_BPP, while NBIE is +0x12. Default BPP=2; 600x600 variant=1; 2400x600 variant=4.',
                            '0x10010398 -> 0x100104c8 is a different constructor path; its missing stores do not establish missing START_PAGE fields.',
                            'The saved 0x10009d34 decompilation stops at the indirect switch and omitted these handlers.'],
                limits=['Static source/dataflow proof, not proof of a live page.',
                        'Page items use low 16 bits. Malformed reserved lengths and physical timing still require separate analysis.'])
    out=ROOT/'analysis/hardware-boundary/zjs-direct-work'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Direct ZjStream page work construction','',f"Status: **{report['status']}**. Offline ELF-byte verification only.",'',report['conclusion'],'']
    lines += ['- '+x for x in report['correction']]
    lines += ['', '| Item | ID | Work offset | Target |','|---|---|---|---|']
    lines += [f"| {r['item']} | {r['item_id']} | {r['work_offset']} | {r['switch_target']} |" for r in fields]
    lines += ['', '| Check | Address | Bytes | Status | Meaning |','|---|---|---|---|---|']
    lines += [f"| {c['name']} | {c.get('address','—')} | {c.get('bytes','—')} | {c['status']} | {c['meaning']} |" for c in checks]
    lines += ['','## Limits','']+['- '+x for x in report['limits']]
    out.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(f"direct work status={report['status']} checks={len(checks)} cases={len(cases)}")
    for c in checks:
        if c['status']!='present': print(c)
    return int(report['status']!='pass')
if __name__=='__main__': raise SystemExit(main())
