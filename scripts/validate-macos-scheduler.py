#!/usr/bin/env python3
"""Stage and run a disposable, strictly sandboxed macOS CUPS scheduler.

Prepare as the ordinary user; run the staged copy with administrator privileges
because Apple's cupsd is root-executable only. Every queue, socket, spool and
helper is under the supplied temporary directory. The only backend is compiled
against our fd-only fake USB process. This NEVER uses the installed scheduler,
real USB backend, device discovery or a real printer.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent

def run(args, ok=True, **kw):
    r=subprocess.run([str(a) for a in args],capture_output=True,timeout=45,**kw)
    if ok and r.returncode: raise AssertionError(f'{args}: {r.stderr.decode(errors="replace")} {r.stdout.decode(errors="replace")}')
    return r

def prepare(area):
    assert os.getuid()!=0 and area.is_absolute() and str(area).startswith('/private/tmp/hp1020-')
    area.mkdir(mode=0o755)
    for name in ('bin/backend','bin/filter','bin/daemon','etc/ppd','state','cache','spool','tmp','runtime'):
        (area/name).mkdir(parents=True,exist_ok=True)
    run(['zsh',ROOT/'scripts/rebuild-runtime-from-vendor.sh',area/'runtime'])
    flags=['-O2','-Wno-deprecated-declarations','-I',ROOT/'files/macos']
    run(['clang',*flags,f'-DTEST_ROOT={json.dumps(str(area))}',ROOT/'scripts/tests/hp1020-fake-usb.c','-lcups','-o',area/'fake-usb'])
    run(['clang',*flags,f'-DHP1020_BASE={json.dumps(str(area))}',f'-DHP1020_USB={json.dumps(str(area/"fake-usb"))}',ROOT/'files/macos/hp1020-backend.c','-lcups','-o',area/'bin/backend/hp1020'])
    for name in ('cgpdftoraster','cgtexttopdf','cgimagetopdf','gziptoany'):
        (area/'bin/filter'/name).symlink_to('/usr/libexec/cups/filter/'+name)
    (area/'bin/daemon/cups-exec').symlink_to('/usr/libexec/cups/daemon/cups-exec')
    (area/'printer.ppd').write_text((ROOT/'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd').read_text().replace('/Library/Printers/hp1020',str(area)))
    # Import fixture construction only; importing does not start its suite.
    import importlib.util
    spec=importlib.util.spec_from_file_location('printing',ROOT/'scripts/validate-macos-printing.py')
    printing=importlib.util.module_from_spec(spec);spec.loader.exec_module(printing)
    printing.make_pdf(area/'pages.pdf')
    (area/'cups-files.conf').write_text(f'''SystemGroup admin
User _lp
Group _lp
ServerRoot {area}/etc
StateDir {area}/state
ServerKeychain {area}/state/ssl
RequestRoot {area}/spool
TempDir {area}/tmp
CacheDir {area}/cache
ServerBin {area}/bin
DataDir /usr/share/cups
DocumentRoot /usr/share/doc/cups
AccessLog {area}/access.log
ErrorLog {area}/error.log
PageLog {area}/page.log
Printcap {area}/printcap
Sandboxing strict
''')
    (area/'cupsd.conf').write_text(f'''Listen {area}/cups.sock
Browsing Off
WebInterface No
LogLevel debug2
IdleExitTimeout 0
PreserveJobHistory Yes
PreserveJobFiles No
PageLogFormat %p %j %P %C
<Location />
Order allow,deny
Allow all
</Location>
<Policy default>
<Limit All>
Order allow,deny
Allow all
</Limit>
</Policy>
''')
    shutil.copy2(__file__,area/'run.py')
    sources=[Path(__file__),ROOT/'scripts/tests/hp1020-fake-usb.c',ROOT/'scripts/rebuild-runtime-from-vendor.sh',
             ROOT/'files/macos/hp1020-backend.c',ROOT/'files/macos/hp1020-common.h',ROOT/'files/macos/rastertohp1020.c',
             ROOT/'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd']
    sources += printing.INPUTS  # Includes fixture construction and every linked vendor source.
    (area/'sources.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print('Staged isolated scheduler test at',area)

def exercise(area):
    assert os.getuid()==0 and Path(__file__).resolve()==area/'run.py'
    assert str(area).startswith('/private/tmp/hp1020-')
    # Explicit isolated destinations on every client command; no default server.
    env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','CUPS_SERVER':str(area/'cups.sock'),'HOME':str(area),'LC_ALL':'C'}
    uid=int(run(['id','-u','_lp']).stdout);gid=int(run(['id','-g','_lp']).stdout)
    for directory,dirs,files in os.walk(area):
        for name in dirs+files:
            p=Path(directory)/name
            if not p.is_symlink(): os.chown(p,0,0)
    os.chown(area,0,0);os.chmod(area,0o755)
    for name in ('tmp','cache','spool'):os.chown(area/name,uid,gid);os.chmod(area/name,0o700)
    run(['/usr/sbin/cupsd','-t','-c',area/'cupsd.conf','-s',area/'cups-files.conf'],env=env)
    log=(area/'daemon.log').open('wb')
    daemon=subprocess.Popen(['/usr/sbin/cupsd','-f','-c',str(area/'cupsd.conf'),'-s',str(area/'cups-files.conf')],stdout=log,stderr=log,env=env)
    checks=[]
    def passed(text):checks.append(text);print('PASS:',text,flush=True)
    def wait(condition,seconds=40):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if daemon.poll() is not None:raise AssertionError('Isolated scheduler stopped')
            if condition():return
            time.sleep(.1)
        raise AssertionError('Timed out waiting for isolated CUPS')
    def events():
        p=area/'tmp/events'
        return [line.split() for line in p.read_text().splitlines()] if p.exists() else []
    def submit(copies=1):
        result=run(['lp','-h',area/'cups.sock','-d','Offline_HP1020','-n',str(copies),'-o','PageSize=A4',area/'pages.pdf'],env=env)
        return re.search(rb'Offline_HP1020-(\d+)',result.stdout)[1].decode()
    def pending():return run(['lpstat','-h',area/'cups.sock','-W','not-completed','-o','Offline_HP1020'],env=env).stdout.decode()
    def mode(value):
        (area/'tmp/mode').write_text(value);os.chmod(area/'tmp/mode',0o644)
    def queue():return run(['lpstat','-h',area/'cups.sock','-p','Offline_HP1020','-l'],env=env).stdout.decode()
    try:
        wait(lambda:(area/'cups.sock').exists())
        run(['lpadmin','-h',area/'cups.sock','-p','Offline_HP1020','-v','hp1020://Hewlett-Packard/HP%20LaserJet%201020?serial=OFFLINE','-P',area/'printer.ppd','-E'],env=env)
        run(['lpadmin','-h',area/'cups.sock','-p','Offline_HP1020','-o','multiple-document-handling-default=separate-documents-collated-copies','-o','printer-error-policy=stop-printer'],env=env)
        mode('paper');job=submit(4)
        wait(lambda:any(e[0]=='received' and e[1]==job for e in events()))
        wait(lambda:'media-empty' in queue() or 'Out of paper' in queue())
        assert 'Offline_HP1020-'+job in pending()
        records=[e for e in events() if e[0]=='received' and e[1]==job]
        assert records[0][2]=='12' and int(records[0][3])==uid
        # Preserve the scheduler's actual generated strict profile as evidence.
        profiles=list((area/'tmp').glob('*'))
        profile=next(p for p in profiles if p.is_file() and p.stat().st_size<100000 and b'(deny default)' in p.read_bytes())
        shutil.copy2(profile,area/'strict-profile.sb')
        passed('real CUPS schedules four complete copies as _lp under its generated strict sandbox and keeps paper-out job active')
        others=[submit() for _ in range(4)]
        wait(lambda:len(pending().splitlines())==5)
        assert sum(e[0]=='open' for e in events())==1
        passed('five submitted documents remain in CUPS with only the first using the transport')
        mode('ok');(area/'tmp/release').touch();os.chmod(area/'tmp/release',0o644)
        wait(lambda:not pending())
        ev=events();assert [e[1] for e in ev if e[0]=='received']==[job,*others]
        active=0
        for e in ev:
            if e[0]=='open':active+=1;assert active==1
            if e[0]=='closed':active-=1
        assert active==0
        passed('clearing paper-out completes the first job and CUPS serializes the other four without duplicates')
        (area/'tmp/release').unlink();mode('paper');cancelled=submit()
        wait(lambda:any(e[0]=='received' and e[1]==cancelled for e in events()))
        run(['cancel','-h',area/'cups.sock','Offline_HP1020-'+cancelled],env=env)
        wait(lambda:any(e[0]=='reset' and e[1]==cancelled for e in events()))
        wait(lambda:not pending())
        passed('CUPS cancellation reaches the backend, requests buffer reset and removes the active job')
        mode('fail');failed=submit()
        wait(lambda:any(e[0]=='failure' and e[1]==failed for e in events()))
        wait(lambda:'Job held' in queue() or 'held' in pending().lower())
        time.sleep(1)
        assert sum(e[0]=='open' and e[1]==failed for e in events())==1
        assert 'Offline_HP1020-'+failed in pending()
        passed('a transport failure is held by CUPS without replay')
        run(['cancel','-h',area/'cups.sock','Offline_HP1020-'+failed],env=env)
        # Sandboxing must be applied, not merely present in a configuration file.
        error=(area/'error.log').read_text()
        assert 'profile=' in error and '(deny default)' in (area/'strict-profile.sb').read_text()
        assert 'Sandboxing off' not in (area/'cups-files.conf').read_text()
        assert not re.search(r'(Unable to.*sandbox|sandbox_init.*failed)',error,re.I)
        data={'checks':checks,'count':len(checks),'source_sha256':json.loads((area/'sources.json').read_text()),
              'host_macos':run(['sw_vers','-productVersion']).stdout.decode().strip(),'cups_scheduler':'real isolated macOS cupsd',
              'sandbox':'strict; scheduler-generated profile preserved with raw test files','transport':'native fd-only fixture',
              'filter_backend_uid':uid,'installed_scheduler_changed':False,'printer_contact':False,'physical_print_test':False,
              'evidence_sha256':{n:hashlib.sha256((area/n).read_bytes()).hexdigest() for n in ('strict-profile.sb','error.log','tmp/events','page.log')}}
        (area/'result.json').write_text(json.dumps(data,indent=2)+'\n');os.chmod(area/'result.json',0o644)
    finally:
        # Explicitly cancel only this disposable server's fixture jobs first.
        if daemon.poll() is None:
            run(['cancel','-h',area/'cups.sock','-a','Offline_HP1020'],ok=False,env=env)
        daemon.terminate()
        try:daemon.wait(timeout=10)
        except subprocess.TimeoutExpired:daemon.kill();daemon.wait()
        log.close()
        # Leave bounded evidence readable by the caller for investigation.
        for name in ('error.log','daemon.log','page.log','tmp/events','strict-profile.sb'):
            p=area/name
            if p.exists():os.chmod(p,0o644)
        os.chmod(area/'tmp',0o755)

if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1] in ('--prepare','--exercise')
    (prepare if sys.argv[1]=='--prepare' else exercise)(Path(sys.argv[2]).resolve())
