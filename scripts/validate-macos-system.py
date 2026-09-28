#!/usr/bin/env python3
"""Verify the real Mac scheduler using a temporary queue and fd-only transport.

For macOS versions that ignore alternate cupsd file settings. Preparation is
unprivileged; the staged administrator runner installs only uniquely named test
files/queue, removes them in finally, and never invokes discovery or real USB.
The existing printer queue and global CUPS configuration are not changed.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
SERVER='/private/var/run/cupsd'

def run(args,ok=True,**kw):
    result=subprocess.run([str(a) for a in args],capture_output=True,timeout=45,**kw)
    if ok and result.returncode:
        raise AssertionError(f'{args}: {result.stderr.decode(errors="replace")} {result.stdout.decode(errors="replace")}')
    return result

def prepare(area):
    spec=importlib.util.spec_from_file_location('scheduler',ROOT/'scripts/validate-macos-scheduler.py')
    scheduler=importlib.util.module_from_spec(spec);spec.loader.exec_module(scheduler)
    scheduler.prepare(area)
    tag=os.urandom(5).hex()
    settings={'tag':tag,'queue':'HP1020_Offline_'+tag,'backend':'hp1020verify'+tag,
              'base':'/Library/Printers/hp1020-verify-'+tag,
              'scratch':'/private/var/spool/cups/tmp/hp1020-verify-'+tag}
    base=Path(settings['base']);scratch=Path(settings['scratch'])
    flags=['-O2','-Wno-deprecated-declarations','-I',ROOT/'files/macos']
    run(['clang',*flags,f'-DTEST_ROOT={json.dumps(str(scratch))}',
         f'-DTEST_SANDBOX_PROBE={json.dumps(str(base/"sandbox-probe"))}',
         ROOT/'scripts/tests/hp1020-fake-usb.c','-lcups','-o',area/'fake-usb'])
    run(['clang',*flags,f'-DHP1020_BASE={json.dumps(str(base))}',
         f'-DHP1020_USB={json.dumps(str(base/"fake-usb"))}',
         ROOT/'files/macos/hp1020-backend.c','-lcups','-o',area/'native-backend'])
    launcher=area/'launcher.c'
    launcher.write_text('#include <stdlib.h>\n#include <unistd.h>\nint main(int n,char **a){\n'
        'if(n==1)return 0;\nif(n<6||n>7)return 3;\n'
        'setenv("DEVICE_URI","hp1020://Hewlett-Packard/HP%20LaserJet%201020?serial=OFFLINE",1);\n'
        f'execv({json.dumps(str(base/"native-backend"))},a);return 3;}}\n')
    run(['clang','-O2',launcher,'-o',area/'launcher'])
    for name in ['fake-usb','native-backend','launcher']:
        run(['codesign','--force','--sign','-',area/name])
    (area/'printer.ppd').write_text((ROOT/'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd').read_text().replace('/Library/Printers/hp1020',str(base)))
    (area/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    sources=json.loads((area/'sources.json').read_text())
    sources[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (area/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    shutil.copy2(__file__,area/'run.py')
    print('Prepared temporary system queue test:',area)

def exercise(area):
    assert os.getuid()==0 and Path(__file__).resolve()==area/'run.py'
    assert str(area).startswith('/private/tmp/hp1020-')
    settings=json.loads((area/'settings.json').read_text());tag=settings['tag']
    assert re.fullmatch('[a-f0-9]{10}',tag)
    name='HP1020_Offline_'+tag
    base=Path('/Library/Printers/hp1020-verify-'+tag)
    scratch=Path('/private/var/spool/cups/tmp/hp1020-verify-'+tag)
    backend=Path('/usr/libexec/cups/backend/hp1020verify'+tag)
    assert not any(p.exists() for p in [base,scratch,backend])
    env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','CUPS_SERVER':SERVER,'HOME':'/var/root','LC_ALL':'C'}
    def cups(command,*args,ok=True):return run([command,'-h',SERVER,*args],ok=ok,env=env)
    assert not cups('lpstat','-W','not-completed','-o').stdout.strip(), 'Finish existing print jobs before this check.'
    assert cups('lpstat','-p',name,ok=False).returncode, 'Test queue already exists.'
    uid=int(run(['id','-u','_lp']).stdout);gid=int(run(['id','-g','_lp']).stdout)
    checks=[];jobs=[];created=False;complete=False
    snapshots=area/'evidence';snapshots.mkdir()
    def passed(text):checks.append(text);print('PASS:',text,flush=True)
    def events():
        p=scratch/'tmp/events'
        return [x.split() for x in p.read_text().splitlines()] if p.exists() else []
    def pending():return cups('lpstat','-W','not-completed','-o',name).stdout.decode()
    def queue():return cups('lpstat','-p',name,'-l').stdout.decode()
    def processes():
        found=[]
        for line in run(['ps','-axo','pid=,command=']).stdout.decode().splitlines():
            pid,command=line.strip().split(None,1)
            if str(base)+'/' in command or backend.name+'://offline' in command:
                found.append((int(pid),command))
        return found
    def wait(condition,seconds=45):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if condition():return
            time.sleep(.15)
        raise AssertionError('Timed out: '+queue()+'\n'+pending()+'\n'+repr(events()))
    def mode(value):
        (scratch/'tmp/mode').write_text(value);os.chmod(scratch/'tmp/mode',0o644)
    def submit(copies=1):
        result=cups('lp','-d',name,'-n',copies,'-o','PageSize=A4',area/'pages.pdf')
        job=re.search(rb'-(\d+) ',result.stdout)[1].decode();jobs.append(job);return job
    try:
        base.mkdir(mode=0o755);shutil.copytree(area/'runtime',base/'runtime')
        for item in ['fake-usb','native-backend','printer.ppd']:
            shutil.copy2(area/item,base/item)
        for directory,dirs,files in os.walk(base):
            for item in dirs+files:os.chown(Path(directory)/item,0,0)
        scratch.mkdir(mode=0o755);(scratch/'tmp').mkdir(mode=0o700);os.chown(scratch/'tmp',uid,gid)
        probe=base/'sandbox-probe';probe.write_bytes(b'');os.chmod(probe,0o666)
        # Establish ordinary _lp permissions separately from the CUPS sandbox.
        child=os.fork()
        if child==0:
            try:
                os.setgroups([gid]);os.setgid(gid);os.setuid(uid)
                with probe.open('ab') as f:f.write(b'outside-cups\n')
                os._exit(0)
            except BaseException:os._exit(1)
        assert os.waitpid(child,0)[1]==0 and probe.read_bytes()==b'outside-cups\n'
        shutil.copy2(area/'launcher',backend);os.chown(backend,0,0);os.chmod(backend,0o755)
        run(['cupstestppd','-q',base/'printer.ppd'])
        cups('lpadmin','-p',name,'-v',backend.name+'://offline','-P',base/'printer.ppd')
        created=True
        cups('lpadmin','-p',name,'-o','printer-is-shared=false','-o','multiple-document-handling-default=separate-documents-collated-copies','-o','printer-error-policy=stop-printer')
        cups('cupsenable',name);cups('cupsaccept',name)
        mode('paper');job=submit(4)
        wait(lambda:any(e[0]=='received' and e[1]==job for e in events()))
        wait(lambda:'media-empty' in queue() or 'Out of paper' in queue())
        assert name+'-'+job in pending()
        ev=events();record=next(e for e in ev if e[0]=='received' and e[1]==job)
        assert record[2]=='12' and int(record[3])==uid
        assert any(e[0]=='sandbox-denied' and e[1]==job for e in ev)
        assert probe.read_bytes()==b'outside-cups\n'
        (snapshots/'paper-queue.txt').write_text(queue()+pending())
        # Capture only this fixture job's generated profiles, if exposed.
        for p in scratch.parent.iterdir():
            if p.is_file() and p.stat().st_size<100000:
                data=p.read_bytes()
                if b'(deny default)' in data and f'd{int(job):05d}-'.encode() in data:
                    (snapshots/('profile-'+p.name+'.sb')).write_bytes(data)
        passed('real macOS queue renders four three-page copies as _lp; its sandbox denies a write otherwise allowed to _lp; paper-out keeps the job active')
        others=[submit() for _ in range(4)]
        wait(lambda:len(pending().splitlines())==5)
        assert sum(e[0]=='open' for e in events())==1
        (snapshots/'five-jobs.txt').write_text(pending())
        passed('five documents stay in the normal queue with only one using the fake transport')
        mode('ok');(scratch/'tmp/release').touch();os.chmod(scratch/'tmp/release',0o644)
        wait(lambda:not pending())
        ev=events();assert [e[1] for e in ev if e[0]=='received']==[job,*others]
        active=0
        for e in ev:
            if e[0]=='open':active+=1;assert active==1
            if e[0]=='closed':active-=1
        assert active==0
        passed('paper recovery completes all five jobs in order without concurrent transports or duplicate output')
        (scratch/'tmp/release').unlink();mode('paper');cancelled=submit()
        wait(lambda:any(e[0]=='received' and e[1]==cancelled for e in events()))
        cups('cancel',name+'-'+cancelled)
        wait(lambda:any(e[0]=='reset' and e[1]==cancelled for e in events()))
        wait(lambda:not pending())
        wait(lambda:not processes())
        assert any(e[0]=='closed' and e[1]==cancelled for e in events())
        passed('normal CUPS cancellation resets the fake buffer, closes the transport and leaves no helper process before the next job')
        mode('fail');failed=submit()
        wait(lambda:any(e[0]=='failure' and e[1]==failed for e in events()))
        wait(lambda:'Job held' in queue() or 'held' in cups('lpstat','-l','-W','not-completed','-o',name).stdout.decode().lower())
        time.sleep(1)
        assert sum(e[0]=='open' and e[1]==failed for e in events())==1
        assert name+'-'+failed in pending()
        (snapshots/'held-queue.txt').write_text(queue()+pending())
        passed('a failed transfer is held by the actual scheduler without automatic replay')
        cups('cancel',name+'-'+failed)
        complete=True
    finally:
        if created:
            cups('cancel','-a',name,ok=False)
            cups('lpadmin','-x',name)
        # A failed test must not leave an orphan that still owns fixture files.
        end=time.monotonic()+3
        while processes() and time.monotonic()<end:time.sleep(.1)
        survivors=processes()
        if survivors:
            (snapshots/'cleanup-survivors.json').write_text(json.dumps(survivors,indent=2)+'\n')
            for pid,command in reversed(survivors):
                try:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass
            time.sleep(.2)
            complete=False
        if (scratch/'tmp').exists():
            for p in (scratch/'tmp').iterdir():
                if p.is_file():shutil.copy2(p,snapshots/p.name)
        if backend.exists():backend.unlink()
        if base.exists():shutil.rmtree(base)
        if scratch.exists():shutil.rmtree(scratch)
        for p in snapshots.iterdir():os.chmod(p,0o644)
        assert cups('lpstat','-p',name,ok=False).returncode
        assert not processes(), 'Test processes remained after cleanup.'
        assert not survivors, 'Test required administrator cleanup; not a passing lifecycle.'
    if complete:
        report={'count':len(checks),'checks':checks,'source_sha256':json.loads((area/'sources.json').read_text()),
                'host_macos':run(['sw_vers','-productVersion']).stdout.decode().strip(),
                'cups_scheduler':'installed macOS scheduler, uniquely named temporary fake queue',
                'filter_backend_uid':uid,'sandbox_negative_control':True,'raw_evidence':str(area),
                'temporary_queue_removed':True,'temporary_components_removed':True,
                'existing_queue_changed':False,'global_cups_configuration_changed':False,
                'printer_contact':False,'physical_print_test':False,
                'evidence_sha256':{str(p.relative_to(area)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(snapshots.iterdir()) if p.is_file()}}
        (area/'result.json').write_text(json.dumps(report,indent=2)+'\n');os.chmod(area/'result.json',0o644)

if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1] in ('--prepare','--exercise')
    (prepare if sys.argv[1]=='--prepare' else exercise)(Path(sys.argv[2]).resolve())
