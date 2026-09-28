#!/usr/bin/env python3
"""Test native components under profiles emitted by pinned Apple CUPS source.

This is a current-user sandbox experiment, NOT actual cupsd or _lp execution.
No admin password is needed, but the invoking environment must permit applying
macOS sandbox profiles. Only a compiled fake transport is executed. Supply the
pinned process.c file as an argument; its hash gates all source extraction.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
CUPS_SOURCE_SHA256='0074e1403f3e3c1c5e789af10ab3b75a72a0a13b188446e84e2054bd322295b7'
CUPS_SOURCE_URL='https://raw.githubusercontent.com/apple/cups/master/scheduler/process.c'
PREFIX=r'''
#include <cups/cups.h>
#include <cups/http.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/stat.h>
#define HAVE_SANDBOX_H 1
#define CUPSD_SANDBOXING_OFF 0
#define CUPSD_SANDBOXING_STRICT 1
#define CUPSD_SANDBOXING_RELAXED 2
#define CUPSD_LOG_DEBUG 2
#define CUPSD_LOG_DEBUG2 3
#define CUPSD_LOG_EMERG 1
#define cupsdLogMessage(...) ((void)0)
#define cupsArrayFirst(x) NULL
#define cupsArrayNext(x) NULL
typedef struct { http_addr_t address; } cupsd_listener_t;
static int UseSandboxing=1,Sandboxing=1,RunUser=0,Group,LogLevel=3;
static char *ServerBin,*CacheDir,*RequestRoot,*ServerRoot,*StateDir,*TempDir;
static char *cupsd_requote(char*,const char*,size_t);
'''
MAIN=r'''
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    Group=getgid();ServerBin="/usr/libexec/cups";
    CacheDir=argv[1];RequestRoot=argv[1];ServerRoot="/private/etc/cups";
    StateDir="/private/etc/cups";TempDir=argv[1];
    char *p=cupsdCreateProfile(1,atoi(argv[2]));
    if(!p)return 1;puts(p);free(p);return 0;
}
'''

def run(args,ok=True,**kwargs):
    result=subprocess.run([str(a) for a in args],capture_output=True,timeout=60,**kwargs)
    if ok and result.returncode:raise AssertionError(f'{args}: {result.stderr.decode(errors="replace")}')
    return result

def main(source):
    assert os.getuid()!=0, 'This test deliberately uses the current user, not root.'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==CUPS_SOURCE_SHA256, 'Pinned Apple CUPS source mismatch'
    text=source.read_text()
    function=text[text.index('void *\t'):text.index("/*\n * 'cupsdDestroyProfile")]
    helper=text[text.rindex('static char'):text.rindex('#endif /* HAVE_SANDBOX_H */')]
    # Keep raw evidence for agent recovery; all documents are generated fixtures.
    parent=Path(tempfile.mkdtemp(prefix='hp1020-sandbox-',dir='/private/tmp'))
    spec=importlib.util.spec_from_file_location('scheduler',ROOT/'scripts/validate-macos-scheduler.py')
    scheduler=importlib.util.module_from_spec(spec);spec.loader.exec_module(scheduler)
    area=parent/'stage';scheduler.prepare(area)
    builder=area/'profile-builder.c';binary=area/'profile-builder'
    builder.write_text(PREFIX+function+helper+MAIN)
    run(['clang','-Wno-deprecated-declarations',builder,'-lcups','-o',binary])
    for name,network in [('filter',0),('backend',1)]:
        generated=Path(run([binary,area/'tmp',network]).stdout.decode().strip())
        shutil.copy2(generated,area/(name+'.sb'));generated.unlink()
    # Both current-user processes use root-mode CUPS policies (RunUser=0),
    # including the deny rule for /Users and no CUPS_TESTROOT exemptions.
    env=dict(os.environ,TMPDIR=str(area/'tmp'))
    render=run(['sandbox-exec','-f',area/'filter.sb','/usr/sbin/cupsfilter','-p',area/'printer.ppd',
                '-d','offline','-e','-i','application/pdf','-m','printer/offline','-n','4',
                '-o','Collate=True','-o','PageSize=A4',area/'pages.pdf'],env=env)
    (area/'output.zjs').write_bytes(render.stdout);(area/'render.log').write_bytes(render.stderr)
    env['DEVICE_URI']='hp1020://Hewlett-Packard/HP%20LaserJet%201020?serial=OFFLINE'
    backend=run(['sandbox-exec','-f',area/'backend.sb',area/'bin/backend/hp1020','901','fixture','offline','1','PageSize=A4',area/'output.zjs'],env=env)
    (area/'backend.log').write_bytes(backend.stderr)
    assert b'Printer confirmed all pages in this job.' in backend.stderr
    events=(area/'tmp/events').read_text().splitlines()
    assert len(events)==3 and events[1].split()[:4]==['received','901','12',str(os.getuid())]
    negative=run(['sandbox-exec','-f',area/'filter.sb','/bin/cat',ROOT/'README.md'],ok=False)
    assert negative.returncode and not negative.stdout and b'Operation not permitted' in negative.stderr
    (area/'negative.log').write_bytes(negative.stderr)
    sources=json.loads((area/'sources.json').read_text())
    sources[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # Reject source edits after staging instead of attributing them to this run.
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items())
    report={'count':3,'checks':['native Mac rendering and encoding of four collated three-page sets under the filter policy',
        'complete native backend/fake transport lifecycle under the backend policy',
        'negative control: policy denies reading the public README in the user directory'],
        'source_sha256':sources,'apple_cups_source_url':CUPS_SOURCE_URL,'apple_cups_source_sha256':CUPS_SOURCE_SHA256,
        'raw_evidence':str(area),'evidence_sha256':{n:hashlib.sha256((area/n).read_bytes()).hexdigest()
             for n in ['pages.pdf','profile-builder.c','filter.sb','backend.sb','render.log','output.zjs','backend.log','negative.log','tmp/events']},
        'uid':os.getuid(),'native_cups_scheduler':False,'lp_user_execution':False,
        'printer_contact':False,'installed_changes':False,'physical_print_test':False}
    (ROOT/'assets/macos-sandbox-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Passed 3 source-derived sandbox checks; actual scheduler/_lp execution remains separate.')
    print('Raw evidence:',area)

if __name__=='__main__':
    assert len(sys.argv)==2,'Usage: validate-macos-sandbox.py PINNED_APPLE_CUPS_PROCESS_C'
    main(Path(sys.argv[1]))
