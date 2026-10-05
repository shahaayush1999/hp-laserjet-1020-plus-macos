#!/usr/bin/env python3
"""Continuous RAM experiment for one complete unmodified two-page host job.

Two initial paint cases; one CPU/image seed each, no host repair,10 natural
stops plus initial and two actual park steps. ELF only; never printer contact.
"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,subprocess,sys,tarfile,tempfile,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'open-firmware/entry-usb-pages-test'
OUT=ROOT/'analysis/boot-handoff/entry-usb-pages'
PREFIX=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
GCC=os.environ.get('HP1020_GCC_PREFIX','/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf')+'-gcc'
# Linked ABI/callback review retains the fixed OUT/page workload graph.
# Changed linked frames add at most64 bytes to its7472-byte ceiling (7536/8192);
# new helpers make only leaf/predicate calls. A changed image needs fresh review.
REVIEWED_TARGET_SHA256='29147c8f911c422f484109f4096d6b70df94fbe57552b599a14e5d2e91c6d71d'
MAIN_START,MAIN_END=0x10003000,0x100351e0
STACK=(0x10014020,8192)
CHECKPOINT_SYMBOLS=(('after-normalization', 'hp1020_entry_after_normalization'), ('pre-c', 'hp1020_entry_before_c'), ('pre-first-output', 'output'), ('pre-first-complete', 'hp1020_image_ring_complete'), ('pre-second-output', 'output'), ('pre-document-event', 'document_event'), ('pre-close', 'hp1020_tusb_adapter_close_input'), ('pre-final-service', 'hp1020_udc_publish_service'), ('pre-finish', 'hp1020_tusb_adapter_finish'), ('park', 'hp1020_entry_park'))


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

BASE_RUNNER_SHA256 = 'ef7cd2ef5c0ee6618002d600efea1a6844ea627a288c3022e766297cda694e1d'
need(sha((ROOT/'scripts/validate-hp1020-entry-usb.py').read_bytes())==BASE_RUNNER_SHA256,
     'unchanged neutral runner helpers required')
base=module('entry_usb_neutral_runner',ROOT/'scripts/validate-hp1020-entry-usb.py')
# Only schedule-neutral byte/ELF/image/snapshot helpers are reused. SOURCE/OUT,
# seals, layout, execution loop and publication below belong to this profile.
command=base.command
def make_input(capture, oracle):
    original=OUT/'fixtures/whole-job.zjs'
    data=original.read_bytes()
    need(data==oracle.STREAM and len(data)==967 and sha(data)==oracle.STREAM_SHA256,
         'unchanged real host job differs from independently frozen literals')
    folder=capture/'input';folder.mkdir()
    for name in ('whole-job.zjs','source.pbm','pixels.bin','encoder-output.json','validation.json'):
        (folder/name).write_bytes((OUT/'fixtures'/name).read_bytes())
    info=dict(source=str(original.relative_to(ROOT)),input_sha256=sha(data),bytes=len(data),
              independent_literal_match=True, normalized=False)
    save(folder/'provenance.json',info);return info
elf_loads=base.elf_loads
file_bytes=base.file_bytes
initial_regions=base.initial_regions
save_snapshot=base.save_snapshot
snapshot_bytes=base.snapshot_bytes
normalized_registers=base.normalized_registers
check_snapshot=base.check_snapshot

def source_files(audit_only=False):
    selected=set()
    for folder in ('entry-usb-pages-test','entry-usb-test','usb-receive-core','image-core','semantic-core',
                   'usb-printer-class','tinyusb-printer-adapter','tinyusb-device',
                   'udc-out','udc-ep0','udc-setup','udc-program','udc-publish'):
        selected.update(p for p in (ROOT/'open-firmware'/folder).rglob('*')
                        if p.is_file() and p.suffix in ('.c','.h','.S','.ld','.py','.json','.tsv','.patch'))
    selected.update((ROOT/'vendor/jbigkit-2.1/libjbig').glob('*.[ch]'))
    selected.update(SOURCE/name for name in ('CONTRACT.md','LIBRARY_SELECTION.md'))
    selected.update(p for p in (ROOT/'open-firmware/entry-usb-test/references/gcc-runtime').rglob('*') if p.is_file())
    selected.update(p for p in (ROOT/'vendor/tinyusb-0.21.0').rglob('*') if p.is_file())
    selected.update(p for p in (ROOT/'open-firmware/entry-ram-test/references/qemu-primary').rglob('*') if p.is_file())
    selected.add(ROOT/'open-firmware/entry-ram-test/literal-oracle.py')
    for name in ('validate-hp1020-entry-usb-pages.py','build-hp1020-entry-usb-pages-target.sh',
                 'hp1020_entry_usb_pages_machine.py','hp1020_entry_usb_pages_qemu.py',
                 'hp1020_entry_usb_pages_audit.py','check-hp1020-entry-usb-pages.py',
                 'validate-hp1020-entry-usb.py','build-hp1020-entry-usb-target.sh',
                 'hp1020_entry_usb_machine.py','hp1020_entry_usb_qemu.py','hp1020_entry_usb_audit.py',
                 'hp1020_entry_machine.py','hp1020_entry_qemu.py','hp1020_entry_audit.py',
                 'hp1020_xtensa_call0.py','hp1020_xtensa_properties.py','hp1020_qemu_ram.py',
                 'check-hp1020-c-compiler-profile.py','prepare-hp1020-tinyusb.py','check-hp1020-entry-usb.py'):
        if name=='check-hp1020-entry-usb-pages.py' and not (ROOT/'scripts'/name).exists():
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

def layout_witness(data,loads,program,capture):
    import csv
    with (SOURCE/'layout-objects.tsv').open() as f:objects=list(csv.DictReader(f,delimiter='\t'))
    with (SOURCE/'layout-fields.tsv').open() as f:fields=list(csv.DictReader(f,delimiter='\t'))
    need(len(objects)==16 and len(fields)==101,'frozen manual table dimensions')
    wanted=[0x4850554c,3,457,16,101]
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
    registers.update(pc=program.entry,physical_ar=list(oracle.PHYSICAL_AR32))
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
        m=machine.EntryUSBPagesMachine(program,initial,registers,checkpoints,model_folder/'traces',observe)
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
        need(len(snapshots)==len(checkpoints)+1,'complete ordered model observations')
        for model_item,q_item in zip(snapshots,q['snapshots'][:len(checkpoints)+1]):
            check_snapshot(initial,folder/'qemu',q_item,program,checkpoints)
            need(normalized_registers(model_item['registers'])==normalized_registers(q_item['registers']),
                 'paired complete CPU observations differ at '+model_item['name'])
            need(snapshot_bytes(model_folder,model_item)==snapshot_bytes(folder/'qemu',q_item),
                 'paired full RAM/stack/islands differ at '+model_item['name'])
        park=q['snapshots'][len(checkpoints)]
        for item in q['snapshots'][len(checkpoints)+1:]:
            need(item['registers']==park['registers'] and snapshot_bytes(folder/'qemu',item)==snapshot_bytes(folder/'qemu',park),
                 'actual repeated park step changed full captured state')
        final=snapshot_bytes(model_folder,snapshots[-1])[MAIN_START]
        stack=final[STACK[0]-MAIN_START:STACK[0]-MAIN_START+STACK[1]]
        changed=[i for i,v in enumerate(stack) if v!=stack_fill]
        report['stack_paint']=dict(initial_byte=stack_fill,changed_bytes=len(changed),
            lowest_changed_address=STACK[0]+min(changed) if changed else None,
            limitation='Stores equal to paint are invisible here; concrete minimum SP/access are separate witnesses.')
        report['status']='pass';report['paired_checkpoints']=len(checkpoints)+1
        print(f'Entry USB real-page RAM {name}: model/QEMU pass',flush=True)
    except BaseException as error:
        report['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if m is not None:
            report['model_partial']=dict(steps=m.steps,pc=m.pc,core_checkpoints=m.seen,observed_checkpoints=[s['name'] for s in snapshots],park_steps=m.park_steps,
                actual_entry_events=m.entry_events,calls=m.calls,access_count=m.access_count,
                pages_checkpoints=list(m.pages_seen),
                pages_observations=list(m.pages_observations),
                pages_api_events=list(m.pages_api_events))
            save_snapshot(model_folder,'failure-state',m.registers_at(m.pc),m.regions_at())
        raise
    finally:
        if m is not None:m.close()
        save(folder/'case.json',report)
    return report

def publish_evidence(capture, report):
    """Keep the raw accepted run recoverable when disposable /tmp disappears."""
    checker=module('entry_capture_checker',ROOT/'scripts/check-hp1020-entry-usb-pages.py')
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
    manifest=dict(schema='hp1020-entry-usb-pages-capture-v1',archive_sha256=sha(payload),
                  archive_bytes=len(payload),members=len(members),
                  member_sha256={n:sha(raw) for n,raw in members.items()})
    cases=report['cases'];steps=sum(c['model']['instructions'] for c in cases)
    minimum=min(c['model']['minimum_sp'] for c in cases)
    lines=['# One entry through a complete real-host two-page RAM job','',
      'Two continuous interpreter/QEMU cases passed the independent raw-capture gate.',
      'All967 original foo2zjs bytes, including PJL, enter one receive generation.',
      'Two distinct pages yield192 exact source pixel bytes and one document event.',
      'Final owned SUCCESS ZLP, next service, empty pump and sole finish precede park.',
      'No physical controller/cache/engine behavior or printing is established.','',
      f'Cases: {len(cases)}; paired checkpoints: {sum(c["paired_checkpoints"] for c in cases)}; observed instructions: {steps}.',
      f'Minimum SP: `{minimum:#x}`; observed stack use: {STACK[0]+STACK[1]-minimum} bytes.','',
      'Exact source and raw evidence seals are in validation.json and capture-manifest.json.','']
    # Stage every potentially failing computation/write before committing the
    # public success report. An interruption during replacement leaves a seal
    # mismatch, never a newly committed report with unfinished publication.
    artifacts=(('capture.tar.gz',payload),
               ('capture-manifest.json',(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()),
               ('validation.md',('\n'.join(lines)+'\n').encode()),
               ('validation.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()))
    for name,raw in artifacts:(OUT/(name+'.partial')).write_bytes(raw)
    for name,_ in artifacts:(OUT/(name+'.partial')).replace(OUT/name)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit-only',action='store_true')
    args=ap.parse_args();capture=Path(tempfile.mkdtemp(prefix='hp1020-entry-usb-pages-',dir='/tmp'))
    print('Entry captures: '+str(capture),flush=True)
    report=dict(status='fail',scope='one-entry continuous USB real-page/fresh-document supplied-RAM experiment',cases=[],capture=str(capture))
    sources={}
    seal_failure=None
    try:
        sources=seal_sources(capture,args.audit_only);report['source_sha256']=sources
        report['independent_capture_gate_present']=(ROOT/'scripts/check-hp1020-entry-usb-pages.py').exists()
        oracle=module('entry_independent_literals',SOURCE/'independent-literals.py')
        report['input']=make_input(capture,oracle)
        target=OUT/'target'
        if target.exists():
            shutil.copytree(target,capture/'target-before-build')
            shutil.rmtree(target)
        try:
            command(['bash',ROOT/'scripts/build-hp1020-entry-usb-pages-target.sh'],capture/'build.log')
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
        audit_module=module('entry_linked_audit',ROOT/'scripts/hp1020_entry_usb_pages_audit.py')
        program,audit=audit_module.audit_target(target/'entry-usb.elf',PREFIX,ROOT/'analysis/sihp1020.elf')
        save(capture/'linked-audit.json',audit);report['linked_audit']=audit
        (capture/'annotated-disassembly.txt').write_text(program.entry_audit_disassembly)
        data=(target/'entry-usb.elf').read_bytes();loads=elf_loads(data)
        need(file_bytes(data,loads,program.symbols['hp1020_usb_runtime_input'],967)==oracle.STREAM,
             'actual linked const input differs from independently frozen literal stream')
        layout=layout_witness(data,loads,program,capture)
        addendum=module('entry_pages_independent_addendum',SOURCE/'literal-addendum.py')
        need([n for n,_ in CHECKPOINT_SYMBOLS]==[row[0] for row in addendum.STOPS] and len(CHECKPOINT_SYMBOLS)==10,
             'exact pre-implementation natural-stop labels')
        checkpoints=[(label,program.symbols[symbol]) for label,symbol in CHECKPOINT_SYMBOLS]
        save(capture/'checkpoints.json',checkpoints);save(capture/'elf-loads.json',loads)
        verify_source_seal(sources)
        if args.audit_only:
            report['status']='audit-only-pass';report['candidate_execution']=False
            print('Entry linked audit passed; candidate has not executed.',flush=True);return
        need(sha(data)==REVIEWED_TARGET_SHA256,
             'rebuilt target differs from the completed source-bound stack/callback review')
        adapter=module('entry_qemu_adapter',ROOT/'scripts/hp1020_entry_usb_pages_qemu.py')
        os.environ['HP1020_ENTRY_QEMU_PRIMARY']=str(ROOT/'open-firmware/entry-ram-test/references/qemu-primary')
        machine=module('entry_concrete_machine',ROOT/'scripts/hp1020_entry_usb_pages_machine.py')
        index=0
        for cpu_index,cpu in enumerate((oracle.CPU,)):
            for paints in oracle.PAINTS:
                report['cases'].append(execute_case(capture,index,cpu_index,cpu,paints,data,loads,
                    program,layout,oracle,adapter,machine,checkpoints));index+=1
                save(capture/'validation.partial.json',report)
        need(len(report['cases'])==2,'both supplied paint cases')
        report['status']='pass';report['candidate_execution']=True
        print('Entry USB real-page RAM: two paired continuous cases captured; independent gate still required.',flush=True)
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
