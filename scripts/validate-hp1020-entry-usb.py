#!/usr/bin/env python3
"""Draft offline continuous entry-owned USB/CPU/stack/BSS and two-document RAM experiment.

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
SOURCE = ROOT/'open-firmware/entry-usb-test'
OUT = ROOT/'analysis/boot-handoff/entry-usb'
PREFIX = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
GCC = os.environ.get('HP1020_GCC_PREFIX', '/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf')+'-gcc'
MAIN_START, MAIN_END = 0x10003000, 0x100351e0
STACK = (0x10014020,8192)
ISLANDS = ((0x10000000,0x184),(0x10000200,0x3c),(0x10000270,0xe0),
           (0x10000370,0x12c),(0x10100020,0x2e4),(0x10100320,0xc))
ENVELOPES = ((MAIN_START,MAIN_END-MAIN_START),)+ISLANDS
CHECKPOINT_SYMBOLS = (('after-normalization','hp1020_entry_after_normalization'),
    ('pre-c','hp1020_entry_before_c'),('pre-close','hp1020_tusb_adapter_close_input'),
    ('pre-final-service','hp1020_udc_publish_service'),
    ('pre-finish','hp1020_tusb_adapter_finish'),
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
    for folder in ('entry-usb-test','usb-receive-core','image-core','semantic-core',
                   'usb-printer-class','tinyusb-printer-adapter','tinyusb-device',
                   'udc-out','udc-ep0','udc-setup','udc-program','udc-publish'):
        selected.update(p for p in (ROOT/'open-firmware'/folder).rglob('*')
                        if p.is_file() and p.suffix in ('.c','.h','.S','.ld','.py','.json','.tsv','.patch'))
    selected.update((ROOT/'vendor/jbigkit-2.1/libjbig').glob('*.[ch]'))
    selected.add(SOURCE/'CONTRACT.md')
    selected.update(p for p in (SOURCE/'references/gcc-runtime').rglob('*') if p.is_file())
    selected.update(p for p in (ROOT/'vendor/tinyusb-0.21.0').rglob('*') if p.is_file())
    selected.update(p for p in (ROOT/'open-firmware/entry-ram-test/references/qemu-primary').rglob('*') if p.is_file())
    selected.add(ROOT/'open-firmware/entry-ram-test/literal-oracle.py')
    for name in ('validate-hp1020-entry-usb.py','build-hp1020-entry-usb-target.sh',
                 'hp1020_entry_usb_machine.py','hp1020_entry_usb_qemu.py','hp1020_entry_usb_audit.py',
                 'hp1020_entry_machine.py','hp1020_entry_qemu.py','hp1020_entry_audit.py',
                 'hp1020_xtensa_call0.py','hp1020_xtensa_properties.py','hp1020_qemu_ram.py',
                 'check-hp1020-c-compiler-profile.py','prepare-hp1020-tinyusb.py','check-hp1020-entry-usb.py'):
        if name=='check-hp1020-entry-usb.py' and not (ROOT/'scripts'/name).exists():
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
    original=ROOT/'analysis/boot-handoff/entry-ram/fixtures/small-black.zjs'
    data=original.read_bytes()
    need(data==oracle.STREAM and len(data)==352 and sha(data)==oracle.STREAM_SHA256,
         'unchanged fixture differs from independent pre-implementation literals')
    folder=capture/'input';folder.mkdir()
    (folder/'small-black.zjs').write_bytes(data)
    info=dict(source=str(original.relative_to(ROOT)),input_sha256=sha(data),bytes=len(data),
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
    need(len(rows)==15,'exact linked load count');return rows


def file_bytes(data,loads,address,count):
    for row in loads:
        if row['address']<=address and address+count<=row['address']+row['filesz']:
            off=row['offset']+address-row['address'];return data[off:off+count]
    raise ValueError(f'not a file-backed target span: {address:#x}+{count}')


def layout_witness(data,loads,program,capture):
    import csv
    with (SOURCE/'layout-objects.tsv').open() as f:objects=list(csv.DictReader(f,delimiter='\t'))
    with (SOURCE/'layout-fields.tsv').open() as f:fields=list(csv.DictReader(f,delimiter='\t'))
    need(len(objects)==16 and len(fields)==101,'frozen manual table dimensions')
    wanted=[0x4850554c,1,457,16,101]
    for r in objects:wanted.extend(int(r[k]) for k in ('id','target32_size','type_alignment'))
    for r in fields:wanted.extend(int(r[k]) for k in ('id','object_id','target32_offset','width'))
    need(len(wanted)==457,'complete manual layout word count')
    raw=file_bytes(data,loads,program.symbols['hp1020_usb_runtime_layout'],457*4)
    actual=list(struct.unpack('>457I',raw))
    need(actual==wanted,'actual compiler fields differ from independently frozen public target32 table')
    result=dict(status='pass',address=program.symbols['hp1020_usb_runtime_layout'],words=actual,
        sha256=sha(raw),expected_sha256={p.name:sha(p.read_bytes()) for p in
            (SOURCE/'layout-objects.tsv',SOURCE/'layout-fields.tsv')})
    save(capture/'layout-witness.json',result);return result


def initial_regions(data,loads,bss_fill,stack_fill,zero_spans):
    regions=[(a,bytearray(((i*29+(a>>4)+0x67)&255) for i in range(n))) for a,n in ENVELOPES]
    def overlay(address,raw):
        for start,buf in regions:
            if start<=address and address+len(raw)<=start+len(buf):
                buf[address-start:address-start+len(raw)]=raw;return
        raise ValueError('load/paint escaped seven exact backing envelopes')
    for row in loads:
        if row['filesz']:overlay(row['address'],data[row['offset']:row['offset']+row['filesz']])
        # NO loader memsz-filesz zero-fill: startup must perform every zero.
    for start,count in zero_spans:overlay(start,bytes([bss_fill])*count)
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


def check_snapshot(initial,folder,item,program,checkpoints):
    actual=snapshot_bytes(folder,item);before=dict(initial);label=item['name']
    regs=normalized_registers(item['registers'])
    if label=='initial':need(actual==before,'exact single supplied initial image');return
    need(regs['pc']==dict(checkpoints)[label],'actual ordered checkpoint PC')
    normalized=dict(lbeg=0,lend=0,lcount=0,windowbase=0,windowstart=1,intenable=0,ps=15)
    need(all(regs[n]==v for n,v in normalized.items()),'normalized privileged own CPU state')
    if label in ('after-normalization','pre-c'):
        need(regs['sar']==0,'startup SAR normalized before C')
    if label in ('after-normalization','pre-c','park'):
        need(regs['logical_ar'][1]==sum(STACK),'own stack top before C or after return')
    writable=[] if label=='after-normalization' else [tuple(x) for x in
        ([(a,a+n) for a,n in program.entry_zero_spans] if label=='pre-c' else program.write_ranges)]
    for start,old in before.items():
        new=actual[start]
        need(all(a==b or any(lo<=start+i<hi for lo,hi in writable)
                 for i,(a,b) in enumerate(zip(old,new))), 'protected byte changed at '+label)
    if label=='pre-c':
        main=actual[MAIN_START]
        for start,count in program.entry_zero_spans:
            off=start-MAIN_START
            need(main[off:off+count]==bytes(count),'full actual BSS not zero at pre-C')
    # The separately authored raw gate checks actual original component bytes,
    # trace/range identities and schedule. Mailbox counters are not the oracle.


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
    initial=initial_regions(data,loads,bss_fill,stack_fill,program.entry_zero_spans)
    registers={k:v for k,v in cpu.items() if k!='name'}
    registers.update(pc=program.entry,physical_ar=list(oracle.physical_ars(cpu_index)))
    save(folder/'initial-registers.json',registers)
    report=dict(case=name,status='fail',cpu_profile=cpu,paints=list(paints),model={},qemu={})
    model_folder=folder/'model';model_folder.mkdir();snapshots=[];m=None
    try:
        def observe(label,regs,regions):
            # Detached copies only: this callback has no reference to machine,
            # no mutator, reset or target-call helper. It persists before checks.
            item=save_snapshot(model_folder,label,regs,regions);snapshots.append(item)
            save(model_folder/'snapshots.json',snapshots)
            check_snapshot(initial,model_folder,item,program,checkpoints)
        m=machine.EntryUSBMachine(program,initial,registers,checkpoints,model_folder/'traces',observe)
        observe('initial',m.registers_at(program.entry),m.regions_at())
        need({k:v for k,v in snapshots[0]['registers'].items() if k!='logical_ar'}==registers,
             'model exact initial CPU state')
        m.run(budget=10000000);report['model']=dict(status='pass',**m.evidence(),snapshots=snapshots)
        m.close();save(model_folder/'result.json',report['model'])
        policy=dict(zero_spans=[list(x) for x in program.entry_zero_spans],
                    owned_stack=list(program.entry_stack),initialized_data_span=list(program.entry_data_span))
        q=adapter.execute(initial,registers,checkpoints,policy,folder/'qemu');report['qemu']=q
        need(q['status']=='pass','independent QEMU run failed; see preserved result')
        need([s['name'] for s in q['snapshots']]==['initial',*(n for n,a in checkpoints),'park-step-1','park-step-2'],
             'complete ordered QEMU observations')
        for model_item,q_item in zip(snapshots,q['snapshots'][:7]):
            check_snapshot(initial,folder/'qemu',q_item,program,checkpoints)
            need(normalized_registers(model_item['registers'])==normalized_registers(q_item['registers']),
                 'paired complete CPU observations differ at '+model_item['name'])
            need(snapshot_bytes(model_folder,model_item)==snapshot_bytes(folder/'qemu',q_item),
                 'paired full RAM/stack/islands differ at '+model_item['name'])
        park=q['snapshots'][6]
        for item in q['snapshots'][7:]:
            need(item['registers']==park['registers'] and snapshot_bytes(folder/'qemu',item)==snapshot_bytes(folder/'qemu',park),
                 'actual repeated park step changed full captured state')
        final=snapshot_bytes(model_folder,snapshots[-1])[MAIN_START]
        stack=final[STACK[0]-MAIN_START:STACK[0]-MAIN_START+STACK[1]]
        changed=[i for i,v in enumerate(stack) if v!=stack_fill]
        report['stack_paint']=dict(initial_byte=stack_fill,changed_bytes=len(changed),
            lowest_changed_address=STACK[0]+min(changed) if changed else None,
            limitation='Stores equal to paint are invisible here; concrete minimum SP/access are separate witnesses.')
        report['status']='pass';report['paired_checkpoints']=7
        print(f'Entry USB RAM {name}: model/QEMU pass',flush=True)
    except BaseException as error:
        report['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if m is not None:
            report['model_partial']=dict(steps=m.steps,pc=m.pc,checkpoints=m.seen,park_steps=m.park_steps,
                actual_entry_events=m.entry_events,calls=m.calls,access_count=m.access_count)
            save_snapshot(model_folder,'failure-state',m.registers_at(m.pc),m.regions_at())
        raise
    finally:
        if m is not None:m.close()
        save(folder/'case.json',report)
    return report


def publish_evidence(capture, report):
    """Keep the raw accepted run recoverable when disposable /tmp disappears."""
    checker=module('entry_capture_checker',ROOT/'scripts/check-hp1020-entry-usb.py')
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
    manifest=dict(schema='hp1020-entry-usb-capture-v1',archive_sha256=sha(payload),
                  archive_bytes=len(payload),members=len(members),
                  member_sha256={n:sha(raw) for n,raw in members.items()})
    cases=report['cases'];steps=sum(c['model']['instructions'] for c in cases)
    minimum=min(c['model']['minimum_sp'] for c in cases)
    lines=['# One entry through USB handling and two RAM documents','',
      'Six continuous interpreter/QEMU cases passed the separately frozen raw-capture gate.',
      'One supplied initial CPU/image is followed by own normalization, BSS initialization,',
      'actual reusable USB control/bulk handling, two documents and one final drain/finish.',
      'All platform observations, cache-copy behavior, settlement and output consumption',
      'are explicitly supplied RAM inputs. No physical USB or printing is established.','',
      f'- Cases: {len(cases)}; paired full checkpoints:42; actual QEMU park steps:12.',
      f'- Concrete instructions across cases: {steps}; lowest observed SP: `{minimum:#x}`.',
      '- Two352-byte streams produce64 actual FF bytes and two original document events.',
      '- The final outstanding OUT owner is separately observed before close, after',
      '  the supplied final zero-length acquisition, and after actual service/pump.',
      '- Exact accepted source/target/tool identities are retained in validation.json.',
      '- capture.tar.gz and capture-manifest.json retain full raw observations.',
      '- Earlier stops and first captures remain distinct in source-snapshots.','',
      'This establishes no actual controller, cache coherence, DMA/IRQ provenance,',
      'hardware loader, cold boot, physical pages, copies or power-cycle recovery.','']
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
    args=ap.parse_args();capture=Path(tempfile.mkdtemp(prefix='hp1020-entry-usb-',dir='/tmp'))
    print('Entry captures: '+str(capture),flush=True)
    report=dict(status='fail',scope='one-entry continuous USB/two-document supplied-RAM experiment',cases=[],capture=str(capture))
    sources={}
    seal_failure=None
    try:
        sources=seal_sources(capture,args.audit_only);report['source_sha256']=sources
        report['independent_capture_gate_present']=(ROOT/'scripts/check-hp1020-entry-usb.py').exists()
        oracle=module('entry_independent_literals',SOURCE/'independent-literals.py')
        report['input']=make_input(capture,oracle)
        target=OUT/'target'
        if target.exists():
            shutil.copytree(target,capture/'target-before-build')
            shutil.rmtree(target)
        try:
            command(['bash',ROOT/'scripts/build-hp1020-entry-usb-target.sh'],capture/'build.log')
        finally:
            if target.exists():shutil.copytree(target,capture/'target')
            # Even an assembly/link stop follows real compiler inputs. Keep
            # available tool/header provenance beside those partial objects.
            try:report['tool_closure']=tool_closure(capture)
            except Exception as error:
                report['partial_tool_closure_error']=str(error)
        report['target_sha256']={str(p.relative_to(target)):sha(p.read_bytes()) for p in sorted(target.rglob('*')) if p.is_file()}
        need('tool_closure' in report,'complete tool/header closure required before linked audit')
        library=json.loads((capture/'target/libgcc/manifest.json').read_text())['archive']
        need(report['tool_closure']['libgcc']==dict(path=library['original_path'],sha256=library['sha256']),
             'captured compiler archive differs from actual compiler-selected tool identity')
        audit_module=module('entry_linked_audit',ROOT/'scripts/hp1020_entry_usb_audit.py')
        program,audit=audit_module.audit_target(target/'entry-usb.elf',PREFIX,ROOT/'analysis/sihp1020.elf')
        save(capture/'linked-audit.json',audit);report['linked_audit']=audit
        (capture/'annotated-disassembly.txt').write_text(program.entry_audit_disassembly)
        data=(target/'entry-usb.elf').read_bytes();loads=elf_loads(data)
        need(file_bytes(data,loads,program.symbols['hp1020_usb_runtime_input'],352)==oracle.STREAM,
             'actual linked const input differs from independently frozen literal stream')
        layout=layout_witness(data,loads,program,capture)
        checkpoints=[(label,program.symbols[symbol]) for label,symbol in CHECKPOINT_SYMBOLS]
        save(capture/'checkpoints.json',checkpoints);save(capture/'elf-loads.json',loads)
        verify_source_seal(sources)
        if args.audit_only:
            report['status']='audit-only-pass';report['candidate_execution']=False
            print('Entry linked audit passed; candidate has not executed.',flush=True);return
        adapter=module('entry_qemu_adapter',ROOT/'scripts/hp1020_entry_usb_qemu.py')
        os.environ['HP1020_ENTRY_QEMU_PRIMARY']=str(ROOT/'open-firmware/entry-ram-test/references/qemu-primary')
        machine=module('entry_concrete_machine',ROOT/'scripts/hp1020_entry_usb_machine.py')
        index=0
        for cpu_index,cpu in enumerate(oracle.CPU_PROFILES):
            for paints in oracle.PAINTS:
                report['cases'].append(execute_case(capture,index,cpu_index,cpu,paints,data,loads,
                    program,layout,oracle,adapter,machine,checkpoints));index+=1
                save(capture/'validation.partial.json',report)
        need(len(report['cases'])==6,'all six supplied profiles')
        report['status']='pass';report['candidate_execution']=True
        print('Entry USB RAM: six paired continuous cases captured; independent gate still required.',flush=True)
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
