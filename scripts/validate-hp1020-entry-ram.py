#!/usr/bin/env python3
"""Draft offline one-entry CPU/stack/BSS and production RAM document experiment.

ELF only: no hardware loader, USB, cache/TLB or engine operation. Each case has
one supplied initial image/CPU state, then read-only observation until own park.
Failures and the exact inputs remain in a fresh capture directory.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'open-firmware/entry-ram-test'
OUT = ROOT/'analysis/boot-handoff/entry-ram'
PREFIX = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
GCC = os.environ.get('HP1020_GCC_PREFIX', '/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf')+'-gcc'
MAIN_START, MAIN_END = 0x10003000, 0x100351e0
ZERO = ((0x1000e000,13512),(0x10016800,114704),(0x10014040,1024))
STACK = (0x10012000,8192)
ISLANDS = ((0x10000000,0x184),(0x10000200,0x3c),(0x10000270,0xe0),
           (0x10000370,0x12c),(0x10100020,0x2e4),(0x10100320,0xc))
ENVELOPES = ((MAIN_START,MAIN_END-MAIN_START),)+ISLANDS
CHECKPOINT_SYMBOLS = (('after-normalization','hp1020_entry_after_normalization'),
    ('pre-c','hp1020_entry_before_c'),('pre-finish','hp1020_usb_document_finish'),
    ('park','hp1020_entry_park'))


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value
    spec.loader.exec_module(value);return value


def command(args,log):
    with Path(log).open('wb') as output:
        result=subprocess.run([str(a) for a in args],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
    need(result.returncode==0,f'command failed ({result.returncode}); preserved {log}')


def source_files(audit_only=False):
    selected=set()
    for folder in ('entry-ram-test','usb-receive-core','image-core','image-pump','semantic-core'):
        selected.update(p for p in (ROOT/'open-firmware'/folder).rglob('*')
                        if p.is_file() and p.suffix in ('.c','.h','.S','.ld','.py','.json'))
    selected.update((ROOT/'vendor/jbigkit-2.1/libjbig').glob('*.[ch]'))
    selected.update(p for p in (SOURCE/'references/qemu-primary').rglob('*') if p.is_file())
    for name in ('validate-hp1020-entry-ram.py','build-hp1020-entry-ram-target.sh',
                 'hp1020_entry_machine.py','hp1020_entry_qemu.py','hp1020_entry_audit.py',
                 'hp1020_xtensa_call0.py','hp1020_xtensa_properties.py','hp1020_qemu_ram.py',
                 'check-hp1020-c-compiler-profile.py','check-hp1020-entry-ram.py'):
        if name=='check-hp1020-entry-ram.py' and not (ROOT/'scripts'/name).exists():
            need(audit_only,'independent capture gate must be frozen before candidate execution')
            continue
        selected.add(ROOT/'scripts'/name)
    return sorted(selected)


def seal_sources(capture,audit_only=False):
    values={}
    for path in source_files(audit_only):
        raw=path.read_bytes();name=str(path.relative_to(ROOT));values[name]=sha(raw)
        dest=capture/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    save(capture/'source-sha256.json',values);return values


def verify_source_seal(values):
    need(all(sha((ROOT/name).read_bytes())==value for name,value in values.items()),
         'source changed during the entry experiment')


def make_input(capture, oracle):
    """Adapt the existing host-generated page fixture, independently of literals."""
    original=ROOT/'analysis/samples/generated/matrix-a4_default.zjs'
    data=original.read_bytes();parts=[];pos=data.index(b'JZJZ')+4
    while pos+16<=len(data):
        n,k,count,reserved,sig=struct.unpack_from('>IIIHH',data,pos)
        need(n>=16 and pos+n<=len(data) and sig==0x5a5a,'existing sample framing')
        parts.append((k,data[pos+16:pos+n],count,reserved));pos+=n
        if k==1:break
    need(parts[0][0]==0 and parts[1][0]==2 and parts[-1][0]==1,'existing sample structure')
    # Unchanged fixture in the preceding image/USB validations. The separate
    # oracle constructs full framing and metadata from literal protocol facts.
    bie=bytes.fromhex('000001000000002000000008000000041000035cfd98ff02ff02')
    need(sha(bie)=='78744d4c1f1f3ac06000192663330834b02b277df26f790aaa340ac322e9cf99',
         'original small black JBIG fixture')
    items=bytearray(parts[1][1]);need(len(items)%12==0,'fixed-size sample items')
    for off in range(0,len(items),12):
        ident=struct.unpack_from('>H',items,off+4)[0]
        if ident in (4,12,13,17,18):
            struct.pack_into('>I',items,off+8,{4:1,12:32,13:8,17:16,18:8}[ident])
    coded=bie[20:]+bytes(16+((-len(bie[20:]))&3))
    body=[parts[0],(2,bytes(items),parts[1][2],parts[1][3]),(4,bie[:20],0,0),
          (5,coded,0,0),(6,b'',0,0),(3,b'',0,0),parts[-1]]
    result=b'JZJZ'+b''.join(struct.pack('>IIIHH',len(p)+16,k,n,r,0x5a5a)+p for k,p,n,r in body)
    need(result==oracle.small_input(),'fixture-derived input differs from independent literal framing')
    fixtures=OUT/'fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    (fixtures/'small-black.zjs').write_bytes(result)
    folder=capture/'input';folder.mkdir()
    for name,raw in (('matrix-a4_default.zjs',data),('small-black.jbg',bie),('small-black.zjs',result)):
        (folder/name).write_bytes(raw)
    info=dict(source=str(original.relative_to(ROOT)),source_sha256=sha(data),
              small_jbig_sha256=sha(bie),input_sha256=sha(result),bytes=len(result),
              independent_literal_match=True)
    save(folder/'provenance.json',info);return info


def elf_loads(data):
    need(data[:6]==b'\x7fELF\x01\x02','ELF32 big-endian')
    phoff=struct.unpack_from('>I',data,28)[0]
    size,count=struct.unpack_from('>HH',data,42);need(size==32,'ELF phdr size')
    rows=[]
    for i in range(count):
        kind,off,va,pa,filesz,memsz,flags,align=struct.unpack_from('>8I',data,phoff+i*size)
        if kind!=1:continue
        need(0<=filesz<=memsz and off+filesz<=len(data),'bounded PT_LOAD')
        rows.append(dict(address=va,physical=pa,offset=off,filesz=filesz,memsz=memsz,flags=flags,align=align))
    need(len(rows)==13,'exact linked load count');return rows


def file_bytes(data,loads,address,count):
    for row in loads:
        if row['address']<=address and address+count<=row['address']+row['filesz']:
            off=row['offset']+address-row['address'];return data[off:off+count]
    raise ValueError(f'not a file-backed target span: {address:#x}+{count}')


def layout_witness(data,loads,program,capture):
    expected=json.loads((SOURCE/'expected-target32.json').read_text())
    wanted=expected['header']+[v for r in expected['records'] for v in r['words']]
    raw=file_bytes(data,loads,program.symbols['hp1020_entry_layout'],260)
    actual=list(struct.unpack('>65I',raw))
    need(actual==wanted,'compiler member offsets differ from frozen independent target32 arithmetic')
    save(capture/'layout-witness.json',dict(status='pass',address=program.symbols['hp1020_entry_layout'],
         words=actual,sha256=sha(raw),expected_sha256=sha((SOURCE/'expected-target32.json').read_bytes())))
    return expected


def initial_regions(data,loads,bss_fill,stack_fill):
    regions=[(a,bytearray(((i*29+(a>>4)+0x67)&255) for i in range(n))) for a,n in ENVELOPES]
    def overlay(address,raw):
        for start,buf in regions:
            if start<=address and address+len(raw)<=start+len(buf):
                buf[address-start:address-start+len(raw)]=raw;return
        raise ValueError('load/paint escaped seven exact backing envelopes')
    for row in loads:
        if row['filesz']:overlay(row['address'],data[row['offset']:row['offset']+row['filesz']])
        # NO loader memsz-filesz zero-fill: startup must perform every zero.
    for start,count in ZERO:overlay(start,bytes([bss_fill])*count)
    overlay(STACK[0],bytes([stack_fill])*STACK[1])
    return [(a,bytes(raw)) for a,raw in regions]


def save_snapshot(folder,label,registers,regions):
    dest=folder/label;dest.mkdir(parents=True)
    rows=[]
    for address,raw in regions:
        name=f'{label}/region-{address:08x}-{len(raw):08x}.bin'
        (folder/name).write_bytes(raw)
        rows.append(dict(start=address,bytes=len(raw),captured_bytes=len(raw),path=name,sha256=sha(raw)))
    item=dict(name=label,status='complete',registers=registers,regions=rows)
    save(dest/'snapshot.json',item);save(dest/'registers.json',registers);return item


def snapshot_bytes(folder,item):
    need(item['status']=='complete','complete checkpoint required');result={}
    for row in item['regions']:
        raw=(folder/row['path']).read_bytes()
        need(len(raw)==row['bytes']==row['captured_bytes'] and sha(raw)==row['sha256'],'raw capture seal')
        need(row['start'] not in result,'unique capture regions');result[row['start']]=raw
    need(set(result)=={a for a,n in ENVELOPES},'full exact region set')
    need(all(len(result[a])==n for a,n in ENVELOPES),'exact full region lengths');return result


def normalized_registers(registers):
    result=registers.copy()
    if 'logical_a' in result:result['logical_ar']=result.pop('logical_a')
    need(result['logical_ar']==[result['physical_ar'][(4*result['windowbase']+i)%32] for i in range(16)],
         'physical/current-window aliases')
    return result


def production_fields(main,layout):
    public={'RECEIVE_GENERATION':'generation','RECEIVE_ISSUED':'issued','RECEIVE_CONSUMED':'consumed',
        'RECEIVE_COUNT':'count','RECEIVE_STOPPED':'stopped','RECEIVE_QUIESCENT':'quiescent',
        'DOCUMENT_FINISHED':'finished','PARSER_DOCUMENTS':'parser_documents','STREAM_PAGES':'stream_pages',
        'PAGES_DRAINED':'pages_drained','DOCUMENTS_COMPLETED':'documents_completed'}
    values={}
    for row in layout['records']:
        if row['name'] not in public:continue
        base,offset,width=row['words'];need(base==1 and width in (1,4),'independent state field schema')
        off=ZERO[0][0]-MAIN_START+offset
        values[public[row['name']]]=int.from_bytes(main[off:off+width],'big')
    return values


def check_snapshot(oracle,initial,folder,item,layout,checkpoints):
    actual=snapshot_bytes(folder,item);before=dict(initial);label=item['name']
    regs=normalized_registers(item['registers'])
    oracle.check_islands({a:before[a] for a,n in ISLANDS},{a:actual[a] for a,n in ISLANDS})
    old,main=before[MAIN_START],actual[MAIN_START]
    if label=='initial':need(actual==before,'exact single supplied initial image');return
    need(regs['pc']==dict(checkpoints)[label],'exact actual checkpoint PC')
    if label=='after-normalization':
        need(actual==before,'normalization changed RAM');oracle.check_registers(regs,'pre-c')
    elif label=='pre-c':oracle.check_pre_c(old,main,regs)
    elif label=='pre-finish':
        oracle.unchanged_outside(old,main,oracle.MUTABLE_RANGES)
        oracle.check_pre_finish(oracle.slice_main(main,oracle.MAILBOX,oracle.MAILBOX_BYTES),production_fields(main,layout))
    elif label=='park':oracle.check_park(old,main,regs)
    else:raise ValueError('unrecognized phase')


def tool_closure(capture):
    paths={'compiler':GCC,'assembler':PREFIX+'-as','linker':PREFIX+'-ld',
           'objdump':PREFIX+'-objdump','nm':PREFIX+'-nm','readelf':PREFIX+'-readelf'}
    libgcc=subprocess.check_output([GCC,'-print-libgcc-file-name'],text=True).strip();paths['libgcc']=libgcc
    for name in ('cc1','as','ld','collect2'):
        value=subprocess.check_output([GCC,'-print-prog-name='+name],text=True).strip()
        path=Path(value)
        if not path.is_absolute():
            found=shutil.which(value);need(found is not None,'GCC subordinate program '+name);path=Path(found)
        paths['gcc-selected-'+name]=str(path)
    result={name:dict(path=str(Path(path).resolve()),sha256=sha(Path(path).read_bytes())) for name,path in paths.items()}
    for name,option in (('configuration','-v'),('specs','-dumpspecs'),('search-directories','-print-search-dirs')):
        command([GCC,option],capture/('compiler-'+name+'.txt'))
        result['compiler-'+name]=sha((capture/('compiler-'+name+'.txt')).read_bytes())
    # Full generated compiler dependency closure, including target standard headers.
    dependencies=set()
    for dep in (OUT/'target').glob('*.d'):
        text=dep.read_text().replace('\\\n',' ')
        dependencies.update(Path(word) for word in text.split(':',1)[1].split())
    system={}
    for path in sorted(dependencies):
        path=path.resolve();raw=path.read_bytes();name=str(path)
        if not path.is_relative_to(ROOT):
            key=sha(name.encode())[:16]+'-'+path.name
            dest=capture/'compiler-headers'/key;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
            system[name]=dict(sha256=sha(raw),snapshot=str(dest.relative_to(capture)))
    need(system,'target standard header dependencies must be preserved')
    result['compiler_headers']=system;save(capture/'tool-closure.json',result);return result


def execute_case(capture,index,cpu_index,cpu,paints,data,loads,program,layout,oracle,adapter,machine,checkpoints):
    bss_fill,stack_fill=paints;name=f'{index:02d}-{cpu["name"]}-{bss_fill:02x}'
    folder=capture/'cases'/name;folder.mkdir(parents=True)
    initial=initial_regions(data,loads,bss_fill,stack_fill)
    registers={k:v for k,v in cpu.items() if k!='name'}
    registers.update(pc=program.entry,physical_ar=oracle.physical_ars(cpu_index))
    save(folder/'initial-registers.json',registers)
    report=dict(case=name,status='fail',cpu_profile=cpu,paints=list(paints),model={},qemu={})
    model_folder=folder/'model';model_folder.mkdir();snapshots=[];m=None
    try:
        def observe(label,regs,regions):
            # Detached copies only: this callback has no reference to machine,
            # no mutator, reset or target-call helper. It persists before checks.
            item=save_snapshot(model_folder,label,regs,regions);snapshots.append(item)
            save(model_folder/'snapshots.json',snapshots)
            check_snapshot(oracle,initial,model_folder,item,layout,checkpoints)
        m=machine.EntryMachine(program,initial,registers,checkpoints,model_folder/'traces',observe)
        observe('initial',m.registers_at(program.entry),m.regions_at())
        need({k:v for k,v in snapshots[0]['registers'].items() if k!='logical_ar'}==registers,
             'model exact initial CPU state')
        m.run(budget=10000000);report['model']=dict(status='pass',**m.evidence(),snapshots=snapshots)
        m.close();save(model_folder/'result.json',report['model'])
        q=adapter.execute(initial,registers,checkpoints,folder/'qemu');report['qemu']=q
        need(q['status']=='pass','independent QEMU run failed; see preserved result')
        need([s['name'] for s in q['snapshots']]==['initial',*(n for n,a in checkpoints),'park-step-1','park-step-2'],
             'complete ordered QEMU observations')
        for model_item,q_item in zip(snapshots,q['snapshots'][:5]):
            check_snapshot(oracle,initial,folder/'qemu',q_item,layout,checkpoints)
            need(normalized_registers(model_item['registers'])==normalized_registers(q_item['registers']),
                 'paired complete CPU observations differ at '+model_item['name'])
            need(snapshot_bytes(model_folder,model_item)==snapshot_bytes(folder/'qemu',q_item),
                 'paired full RAM/stack/islands differ at '+model_item['name'])
        park=q['snapshots'][4]
        for item in q['snapshots'][5:]:
            need(item['registers']==park['registers'] and snapshot_bytes(folder/'qemu',item)==snapshot_bytes(folder/'qemu',park),
                 'actual repeated park step changed full captured state')
        final=snapshot_bytes(model_folder,snapshots[-1])[MAIN_START]
        stack=final[STACK[0]-MAIN_START:STACK[0]-MAIN_START+STACK[1]]
        changed=[i for i,v in enumerate(stack) if v!=stack_fill]
        report['stack_paint']=dict(initial_byte=stack_fill,changed_bytes=len(changed),
            lowest_changed_address=STACK[0]+min(changed) if changed else None,
            limitation='Stores equal to paint are invisible here; concrete minimum SP/access are separate witnesses.')
        report['status']='pass';report['paired_checkpoints']=5
        print(f'Entry RAM {name}: model/QEMU pass',flush=True)
    except BaseException as error:
        report['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if m is not None:
            report['model_partial']=dict(steps=m.steps,pc=m.pc,checkpoints=m.seen,park_steps=m.park_steps)
        raise
    finally:
        if m is not None:m.close()
        save(folder/'case.json',report)
    return report


def publish_evidence(capture, report):
    """Keep the raw accepted run recoverable when disposable /tmp disappears."""
    checker=module('entry_capture_checker',ROOT/'scripts/check-hp1020-entry-ram.py')
    ok,detail=checker.check_capture(capture,ROOT)
    save(capture/'independent-gate.json',dict(ok=ok,detail=detail))
    need(ok,'independent capture gate failed: '+str(detail))
    # Prior build artifacts belong to failure history, not this run's closure.
    members={str(p.relative_to(capture)):p.read_bytes() for p in sorted(capture.rglob('*'))
             if p.is_file() and 'target-before-build' not in p.relative_to(capture).parts}
    need(all(len(raw)<=32*1024*1024 for raw in members.values()) and
         sum(map(len,members.values()))<=128*1024*1024,'bounded recoverable capture members')
    buffer=io.BytesIO()
    with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w') as archive:
            for name,raw in members.items():
                need(not Path(name).is_absolute() and '..' not in Path(name).parts,'relative archive member')
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o644;item.mtime=0
                archive.addfile(item,io.BytesIO(raw))
    payload=buffer.getvalue()
    need(len(payload)<=32*1024*1024,'bounded recoverable capture archive')
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as archive:
        need(archive.getnames()==list(members),'complete archive member set')
        for name,raw in members.items():
            need(archive.extractfile(name).read()==raw,'archive readback: '+name)
    manifest=dict(schema='hp1020-entry-capture-v1',archive_sha256=sha(payload),
                  archive_bytes=len(payload),members=len(members),
                  member_sha256={n:sha(raw) for n,raw in members.items()})
    cases=report['cases'];steps=sum(c['model']['instructions'] for c in cases)
    minimum=min(c['model']['minimum_sp'] for c in cases)
    lines=['# One entry through a RAM document','',
      'Six continuous cases pass the bounded interpreter and independent QEMU,',
      'followed by the separately frozen raw-capture checker. Each case has one',
      'supplied loaded RAM image and CPU state; no later reset, register repair or',
      'host memory write connects its startup, BSS initialization, page and park.','',
      f'- CPU/paint profiles: {len(cases)}; paired checkpoints: 30; actual QEMU park steps: 12.',
      f'- Concrete instructions across cases: {steps}; lowest observed SP: `{minimum:#x}`.',
      '- Full state/memory/mailbox BSS: 129224 bytes; owned stack: 8192 bytes.',
      '- Input: 352 bytes in six supplied RAM fragments; output: 32 literal FF bytes.',
      '- The original document event and pixels precede the explicit finish call.',
      '- Full registers, RAM, stack, guards and inert islands are paired; access',
      '  traces and every debugger command/reply are independently checked.','',
      '`validation.json` records exact tested source/tool/target identities.',
      '`capture.tar.gz` and `capture-manifest.json` preserve the full accepted raw',
      'capture, including copied sources and target headers, after /tmp is lost.',
      'Historical build/audit stops and the first successful run remain separate',
      'in `source-snapshots/`; their recorded source hashes are not rewritten.','',
      'Privilege, exclusively owned mapped RAM, no asynchronous exceptions, RAM',
      'transport completion and immediate software output completion are supplied.',
      'This establishes no physical boot, loader compatibility, cache/DMA, USB,',
      'controller, engine, printing or power-cycle recovery. The open replacement',
      'cannot print yet.']
    # Stage every potentially failing computation/write before committing the
    # public success report. An interruption during replacement leaves a seal
    # mismatch, never a newly committed report with unfinished publication.
    artifacts=(('capture.tar.gz',payload),
               ('capture-manifest.json',(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()),
               ('validation.md',('\n'.join(lines)+'\n').encode()),
               ('validation.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()))
    for name,raw in artifacts:(OUT/(name+'.partial')).write_bytes(raw)
    for name,_ in artifacts:(OUT/(name+'.partial')).replace(OUT/name)
    # The report above is the final operation: no fallible output follows it.


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit-only',action='store_true')
    args=ap.parse_args();capture=Path(tempfile.mkdtemp(prefix='hp1020-entry-ram-',dir='/tmp'))
    print('Entry captures: '+str(capture),flush=True)
    report=dict(status='fail',scope='one-entry standard-ISA RAM experiment',cases=[],capture=str(capture))
    sources={}
    seal_failure=None
    try:
        sources=seal_sources(capture,args.audit_only);report['source_sha256']=sources
        report['independent_capture_gate_present']=(ROOT/'scripts/check-hp1020-entry-ram.py').exists()
        oracle=module('entry_independent_literals',SOURCE/'literal-oracle.py')
        report['input']=make_input(capture,oracle)
        target=OUT/'target'
        if target.exists():
            shutil.copytree(target,capture/'target-before-build')
            shutil.rmtree(target)
        try:
            command(['bash',ROOT/'scripts/build-hp1020-entry-ram-target.sh'],capture/'build.log')
        finally:
            if target.exists():shutil.copytree(target,capture/'target')
            # Even an assembly/link stop follows real compiler inputs. Keep
            # available tool/header provenance beside those partial objects.
            try:report['tool_closure']=tool_closure(capture)
            except Exception as error:
                report['partial_tool_closure_error']=str(error)
        report['target_sha256']={str(p.relative_to(target)):sha(p.read_bytes()) for p in sorted(target.rglob('*')) if p.is_file()}
        need('tool_closure' in report,'complete tool/header closure required before linked audit')
        audit_module=module('entry_linked_audit',ROOT/'scripts/hp1020_entry_audit.py')
        program,audit=audit_module.audit_target(target/'entry-ram.elf',PREFIX,ROOT/'analysis/sihp1020.elf')
        save(capture/'linked-audit.json',audit);report['linked_audit']=audit
        (capture/'annotated-disassembly.txt').write_text(program.entry_audit_disassembly)
        data=(target/'entry-ram.elf').read_bytes();loads=elf_loads(data)
        need(file_bytes(data,loads,program.symbols['hp1020_entry_input'],352)==oracle.small_input(),
             'actual linked const input differs from independently frozen literal stream')
        layout=layout_witness(data,loads,program,capture)
        checkpoints=[(label,program.symbols[symbol]) for label,symbol in CHECKPOINT_SYMBOLS]
        save(capture/'checkpoints.json',checkpoints);save(capture/'elf-loads.json',loads)
        verify_source_seal(sources)
        if args.audit_only:
            report['status']='audit-only-pass';report['candidate_execution']=False
            print('Entry linked audit passed; candidate has not executed.',flush=True);return
        adapter=module('entry_qemu_adapter',ROOT/'scripts/hp1020_entry_qemu.py')
        os.environ['HP1020_ENTRY_QEMU_PRIMARY']=str(SOURCE/'references/qemu-primary')
        machine=module('entry_concrete_machine',ROOT/'scripts/hp1020_entry_machine.py')
        index=0
        for cpu_index,cpu in enumerate(oracle.CPU_PROFILES):
            for paints in oracle.PAINTS:
                report['cases'].append(execute_case(capture,index,cpu_index,cpu,paints,data,loads,
                    program,layout,oracle,adapter,machine,checkpoints));index+=1
                save(capture/'validation.partial.json',report)
        need(len(report['cases'])==6,'all six supplied profiles')
        report['status']='pass';report['candidate_execution']=True
        print('Entry RAM: six paired continuous cases passed; no physical boot or printing proof.',flush=True)
    except BaseException as error:
        report['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc());raise
    finally:
        try:
            if sources:verify_source_seal(sources)
        except Exception as error:
            report['status']='fail';report['source_seal_error']=str(error)
            seal_failure=error
        save(capture/'validation.json',report)
        if seal_failure is not None:raise seal_failure
        if report['status']=='pass':
            try:publish_evidence(capture,report)
            except BaseException as error:
                report['status']='fail';report['publication_error']=str(error)
                save(capture/'validation.json',report)
                raise


if __name__=='__main__':main()
