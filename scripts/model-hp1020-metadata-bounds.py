#!/usr/bin/env python3
"""Verify stock split-allocation item bounds and generated fixture compatibility."""
import json
from pathlib import Path
import runpy
from hp1020_metadata_bounds import metadata_bounds
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
read=runpy.run_path(str(ROOT/'scripts/recover-hp1020-division-decode.py'))['elf_range']
spec=importlib.util.spec_from_file_location('metadata_print_model',ROOT/'scripts/model-hp1020-print-path.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)


def main():
    fixtures={
        0x10009e19:('288106','l16ui a8,a8,12: header reserved bytes'),
        0x10009e1f:('28166708550c','save reserved; remaining payload subtracts it'),
        0x10009e27:('088a022b0a02','allocation argument is reserved, flags=2'),
        0x10009e30:('5824c3','call8 allocator 0x10013140'),
        0x10009e4c:('2b1265dce0','read callback destination is reserved buffer; count is reserved'),
        0x10009e74:('da20db40dc50','remaining payload read goes to separate buffer'),
        0x10009fe5:('2b12652c1267dd305bfed7','START_PAGE builder receives reserved buffer plus original item count'),
        0x10009d24:('8830b144a833754b0263fe44','builder advances by item size and stops by item count, with no remaining-byte bound'),
    }
    checks=[]
    for address,(raw,meaning) in fixtures.items():
        assert read(address,len(bytes.fromhex(raw))).hex()==raw
        checks.append(dict(address=f'0x{address:08x}',bytes=raw,meaning=meaning,status='present'))
    cases=[]
    for path in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
        _,_,chunks,_=m.parse_chunks(path)
        rows=[dict(chunk=c.name,**metadata_bounds(c.payload,c.item_count,c.reserved)) for c in chunks if c.chunk_type in (0,2)]
        cases.append(dict(case=path.stem,status='bounded' if all(r['status']=='bounded' for r in rows) else 'invalid',chunks=rows))
    invalid=[c for c in cases if c['status']=='invalid']
    assert [c['case'] for c in invalid]==['matrix-a4_logical_clip']
    bad=invalid[0]['chunks'][1]
    assert bad['reserved']==156 and bad['item_bytes']==180
    assert [i['id'] for i in bad['items'] if not i['within_reserved']]==[3,6]
    # Boundary checker itself fails closed on truncated headers, invalid sizes,
    # and reserved-over-payload; exact allocation is accepted.
    item=bytes.fromhex('0000000c0012010000001aa8')
    assert metadata_bounds(item,1,12)['status']=='bounded'
    for payload,count,reserved in [(item,1,11),(item,2,12),(item,1,13),(bytes(12),1,12)]:
        assert metadata_bounds(payload,count,reserved)['status']=='invalid'
    report=dict(status='pass',checks=checks,cases=cases,bounded_cases=len(cases)-len(invalid),invalid_cases=len(invalid),
                conclusion='The logical-clip fixture requests 15 items but supplies only 13 in the declared metadata buffer. Paper and media items lie outside that initialized allocation.',
                distinction='The portable core safely parses all 180 payload bytes. That model result is not proof of equivalent stock behavior for this fixture.',
                limitation='Allocator rounding does not establish initialization or contiguity of separately allocated data. Actual erroneous stock output is not predicted or tested.',
                scope='offline analysis; no fixture was sent and no installed runtime was changed')
    out=ROOT/'analysis/open-firmware-model/metadata-bounds'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Stock metadata allocation bounds','',report['scope'],'',report['conclusion'],'',report['distinction'],'',
           f"{report['bounded_cases']} fixtures fit the declared metadata allocation; {report['invalid_cases']} does not.",'',
           '| Fixture | Status |','|---|---|']+[f"| {c['case']} | {c['status']} |" for c in cases]
    lines+=['','## Instruction evidence','', '| Address | Bytes | Meaning |','|---|---|---|']+[f"| {c['address']} | {c['bytes']} | {c['meaning']} |" for c in checks]
    lines+=['',report['limitation'],'']
    out.with_suffix('.md').write_text('\n'.join(lines))
    print(f"metadata bounds: {len(cases)-1} bounded fixtures, 1 expected logical-clip mismatch; 8 stock-byte checks")

if __name__=='__main__':main()
