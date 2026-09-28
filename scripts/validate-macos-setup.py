#!/usr/bin/env python3
"""Test repository setup with isolated Homebrew, admin, CUPS and USB fixtures.

Never runs real package-manager mutations, installation or printer commands.
End users run two zsh scripts. The new driver needs only macOS; Homebrew
fixtures exercise cleanup of ownership records left by earlier versions.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
INPUTS = [ROOT / 'templates/hp1020-print.in', ROOT / 'assets/runtime/sihp1020.dl',
          *(ROOT / 'files/macos').glob('*.c'), *(ROOT / 'files/macos').glob('*.h'),
          ROOT / 'assets/licenses/foo2zjs-COPYING', ROOT / 'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd',
          *(ROOT / 'scripts' / name for name in ('install.sh','uninstall.sh','macos-common.sh',
             'rebuild-runtime-from-vendor.sh','diagnose.sh','print-test.sh')),
          *(ROOT / 'vendor/foo2zjs-source' / name for name in ('foo2zjs.c','zjs.h','jbig.c','jbig.h','jbig_ar.c','jbig_ar.h'))]

def command(args, *, env=None, data=None, ok=True):
    with subprocess.Popen([str(a) for a in args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(data, timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        result = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
    if ok and result.returncode:
        raise AssertionError(f"Failed {args}: {result.stderr.decode(errors='replace')[-3000:]}")
    return result


def write_script(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    path.chmod(0o755)
    return path


def stream(data):
    """Strictly walk the actual output chunks, retaining compressed image bytes."""
    pos = data.index(b"JZJZ") + 4
    chunks = []
    while pos + 16 <= len(data):
        size, kind, count, reserved, signature = struct.unpack_from(">IIIHH", data, pos)
        assert size >= 16 and pos + size <= len(data) and signature == 0x5A5A
        payload = data[pos + 16:pos + size]
        items = {}
        cursor = 0
        for _ in range(count):
            length, ident, typ, param = struct.unpack_from(">IHBB", payload, cursor)
            assert length >= 8 and cursor + length <= len(payload)
            items[ident] = struct.unpack_from(">I", payload, cursor + 8)[0] if typ == 1 else payload[cursor + 8:cursor + length]
            cursor += length
        chunks.append((kind, items, payload))
        pos += size
        if kind == 1:
            break
    assert chunks[0][0] == 0 and chunks[-1][0] == 1
    assert sum(k == 2 for k, _, _ in chunks) == sum(k == 3 for k, _, _ in chunks) > 0
    assert any(k == 5 and body for k, _, body in chunks)
    return chunks


MOCK_BREW = '''#!PYTHON
import json, os, pathlib, sys
state = pathlib.Path(os.environ['MOCK_BREW_STATE'])
data = json.loads(state.read_text())
args = sys.argv[1:]
with open(os.environ['MOCK_CALLS'], 'a') as out:
    out.write('brew ' + ' '.join(args) + '\\n')
assert os.environ.get('HOMEBREW_NO_AUTOREMOVE') == '1'
installed = set(data['formulae'])
deps = {'ghostscript': {'fontlib'}, 'gnu-sed': set(), 'python@3.14': {'pydep'}, 'pydep': set(), 'fontlib': set(), 'other-app': {'fontlib'}, 'unrelated': set(), 'orphan': set()}
cmd = args[0]
if cmd == '--prefix': print(os.environ['MOCK_PREFIX'])
elif cmd == 'list':
    if os.environ.get('MOCK_QUERY_FAIL') == '1': sys.exit(7)
    if '--cask' in args and os.environ.get('MOCK_CASK_QUERY_FAIL') == '1': sys.exit(7)
    print('\\n'.join(sorted(data.get('casks', []) if '--cask' in args else installed)))
elif cmd == 'deps': print('\\n'.join(sorted(set().union(*(deps.get(a, set()) for a in args[1:])))))
elif cmd == 'install':
    installed.add('fontlib')
    if os.environ.get('MOCK_INSTALL_FAIL') != '1':
        installed.update(a for a in args[1:] if not a.startswith('-'))
        installed.update(set().union(*(deps.get(a, set()) for a in args[1:])))
    data['formulae'] = sorted(installed)
    state.write_text(json.dumps(data))
    if os.environ.get('MOCK_INSTALL_FAIL') == '1': sys.exit(6)
elif cmd == 'uses':
    print('\\n'.join(sorted(p for p in installed if args[-1] in deps.get(p, set()))))
elif cmd == 'uninstall':
    if os.environ.get('MOCK_UNINSTALL_FAIL') == '1': sys.exit(8)
    assert not any(args[-1] in deps.get(p, set()) for p in installed), args
    installed.remove(args[-1])
    data['formulae'] = sorted(installed)
    state.write_text(json.dumps(data))
else: raise AssertionError(args)
'''


def main():
    checks, conversions = [], []
    def passed(name):
        checks.append(name)
        print('PASS:', name, flush=True)
    with tempfile.TemporaryDirectory(prefix='hp1020-setup-check-') as folder:
        test = Path(folder)
        clean = {'PATH': SYSTEM_PATH, 'HOME': str(test), 'USER': 'fixture', 'LC_ALL': 'C', 'TMPDIR': str(test)}
        pdf = test / 'fixture.pdf'
        pdf.write_bytes(b'%PDF fixture for submission argument checks only')
        gs, gsed = Path('/opt/homebrew/bin/gs'), Path('/opt/homebrew/bin/gsed')
        def fixture(name, packages=(), existing=True):
            area = test / name
            target, mock, repo = area / 'target', area / 'mock-bin', area / "Dad's repo $(touch UNEXPECTED)"
            home = target / "Users/Dad's home $(touch UNEXPECTED)"
            prefix = target / 'opt/homebrew'
            home.mkdir(parents=True)
            mock.mkdir()
            for part in ('usr/libexec/cups/backend', 'usr/libexec/cups/filter', 'Library/LaunchDaemons', 'private/etc/cups/ppd'):
                (target / part).mkdir(parents=True)
            state = area / 'brew-state.json'
            state.write_text(json.dumps({'formulae': list(packages), 'casks': []}))
            env = dict(clean, HP1020_HOME=str(home), HP1020_USER='dad', MOCK_BREW_STATE=str(state),
                       MOCK_PREFIX=str(prefix), MOCK_CALLS=str(area / 'calls'), MOCK_USB_CALLS=str(area / 'usb-calls'),
                       MOCK_QUEUE=str(area / 'queue-exists'), MOCK_LAUNCH_MARKER=str(area / 'launch-failed'))
            env['MOCK_READY'] = str(target / 'Library/Printers/hp1020/state/ready')
            env['MOCK_QUEUE_PPD'] = str(target / 'private/etc/cups/ppd/HP_LaserJet_1020_Plus.ppd')
            env['MOCK_URI'] = str(area / 'queue-uri')
            env['MOCK_ACCEPTED'] = str(area / 'queue-accepted')
            env['MOCK_ENABLED'] = str(area / 'queue-enabled')
            env['MOCK_REPO'] = str(repo)
            env['MOCK_PYTHON'] = sys.executable
            env['MOCK_ADMIN_RUNNER'] = str(write_script(area / 'admin-runner.py', '''
import os, pathlib, subprocess, sys
script = pathlib.Path(sys.argv[1])
if os.environ.get('MOCK_FATAL_EXPANSION') == '1':
    content = script.read_text()
    line = 'rm -rf "$BASE"'
    assert content.count(line) == 1
    script.write_text(content.replace(line, line + '\\nprint -- "$render_dir/missing-file-"*'))
repo = pathlib.Path(os.environ['MOCK_REPO'])
hidden = repo.with_name(repo.name + '.unavailable')
block_repo = os.environ.get('MOCK_REPO_HIDDEN') == '1'
try:
    if block_repo: repo.rename(hidden)
    sys.exit(subprocess.run(['/bin/zsh', str(script)], env=dict(os.environ, MOCK_ADMIN='1')).returncode)
finally:
    if block_repo: hidden.rename(repo)
'''))
            brew_template = write_script(area / 'brew-template', MOCK_BREW.replace('PYTHON', sys.executable, 1))
            bootstrap = write_script(area / 'bootstrap.py', f'''#!{sys.executable}
import os, pathlib, shutil, sys
prefix = pathlib.Path(os.environ['MOCK_PREFIX'])
if sys.argv[1] == 'install':
    (prefix / 'bin').mkdir(parents=True, exist_ok=True)
    shutil.copy2({str(brew_template)!r}, prefix / 'bin/brew')
    for name, source in [('gs', {str(gs)!r}), ('gsed', {str(gsed)!r})]:
        (prefix / 'bin' / name).symlink_to(source)
    python = prefix / 'opt/python@3.14/bin/python3.14'
    python.parent.mkdir(parents=True)
    python.symlink_to({sys.executable!r})
else:
    assert sys.argv[1] == 'uninstall' and '--force' in sys.argv
    assert '--path=' + str(prefix) in sys.argv
    shutil.rmtree(prefix)
''')
            if existing:
                command([sys.executable, bootstrap, 'install'], env=env)
            curl = f'''#!/bin/zsh
print -r -- "curl $*" >> "$MOCK_CALLS"
args=("$@")
output=""
operation=""
while (( $# )); do
  case "$1" in
    -o) output="$2"; shift 2 ;;
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh) operation=install; shift ;;
    https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh) operation=uninstall; shift ;;
    *) shift ;;
  esac
done
[[ -n "$output" && -n "$operation" ]] || exit 90
print -r -- '#!/bin/sh' > "$output"
print -r -- "exec {shlex.quote(sys.executable)} {shlex.quote(str(bootstrap))} $operation \\\"\\$@\\\"" >> "$output"
'''
            write_script(mock / 'curl', curl)
            common = '''#!/bin/zsh
print -r -- "${0:t} $*" >> "$MOCK_CALLS"
case "${0:t}" in
  id) print "${MOCK_UID:-501}" ;;
  sysctl) print "${MOCK_ARM64:-1}" ;;
  xcrun) [[ "${MOCK_NO_CLT:-0}" == 0 ]] || exit 1; exec /usr/bin/xcrun "$@" ;;
  lpstat)
    if [[ "$1" == -p ]]; then
      [[ -e "$MOCK_QUEUE" ]] || exit 1
      if [[ -e "$MOCK_ENABLED" ]]; then print 'printer HP_LaserJet_1020_Plus is idle'
      else print 'printer HP_LaserJet_1020_Plus disabled since fixture'; fi
    elif [[ "$1" == -v ]]; then
      print -r -- "device for HP_LaserJet_1020_Plus: $(cat "$MOCK_URI")"
    elif [[ "$1" == -a ]]; then
      [[ ! -e "$MOCK_ACCEPTED" ]] || print 'HP_LaserJet_1020_Plus accepting requests'
    elif [[ "${MOCK_PENDING:-0}" == 1 || ( "${MOCK_PENDING_ADMIN:-0}" == 1 && "${MOCK_ADMIN:-0}" == 1 ) ]]; then
      print 'HP_LaserJet_1020_Plus-1 dad 100'
    fi ;;
  lpinfo) [[ "${MOCK_DEVICE:-one}" == one ]] && print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=FAMILY "HP"'; exit 0 ;;
  osascript)
    [[ "${MOCK_ADMIN_FAIL:-0}" != 1 ]] || exit 1
    exec "$MOCK_PYTHON" "$MOCK_ADMIN_RUNNER" "$argv[-1]" ;;
  lpadmin)
    if [[ "$1" == -x ]]; then
      [[ "${MOCK_QUEUE_REMOVE_FAIL:-0}" != 1 ]] || exit 1
      rm -f "$MOCK_QUEUE" "$MOCK_QUEUE_PPD"
    else
      if [[ "${MOCK_LPADMIN_FAIL:-0}" == 1 && ! -e "$MOCK_LAUNCH_MARKER" ]]; then touch "$MOCK_LAUNCH_MARKER"; exit 1; fi
      touch "$MOCK_QUEUE"
      for (( i=1; i<$#; i++ )); do
        if [[ "$argv[$i]" == -v ]]; then print -r -- "$argv[$((i+1))]" > "$MOCK_URI"; fi
        if [[ "$argv[$i]" == -P && "$argv[$((i+1))]" != "$MOCK_QUEUE_PPD" ]]; then
          cp "$argv[$((i+1))]" "$MOCK_QUEUE_PPD"
        fi
      done
    fi ;;
  cupsaccept)
    if [[ "${MOCK_ACCEPT_FAIL:-0}" == 1 && ! -e "$MOCK_LAUNCH_MARKER" ]]; then touch "$MOCK_LAUNCH_MARKER"; exit 1; fi
    touch "$MOCK_ACCEPTED" ;;
  cupsenable)
    if [[ "${MOCK_ENABLE_FAIL:-0}" == 1 && ! -e "$MOCK_LAUNCH_MARKER" ]]; then touch "$MOCK_LAUNCH_MARKER"; exit 1; fi
    touch "$MOCK_ENABLED" ;;
  cupsdisable) rm -f "$MOCK_ENABLED" ;;
  cupsreject) rm -f "$MOCK_ACCEPTED" ;;
  launchctl)
    if [[ "$1" == bootstrap && "${MOCK_LAUNCH_FAIL:-0}" == 1 && ! -e "$MOCK_LAUNCH_MARKER" ]]; then
      touch "$MOCK_LAUNCH_MARKER"; exit 1
    fi
    if [[ "$1" == bootstrap && "${MOCK_NOT_READY:-0}" != 1 ]]; then
      print -r -- "HP1020-SERVICE-2 $PPID" > "$MOCK_READY"
    fi ;;
  cupstestppd)
    if [[ "${MOCK_HEALTH_FAIL:-0}" == 1 && "${MOCK_ADMIN:-0}" == 1 && ! -e "$MOCK_LAUNCH_MARKER" ]]; then touch "$MOCK_LAUNCH_MARKER"; exit 1; fi
    exec /usr/bin/cupstestppd -I filters "$@" ;;
  install)
    if [[ "${MOCK_COPY_FAIL:-0}" == 1 && "$argv[-1]" == */runtime/rastertohp1020 ]]; then exit 1; fi
    args=()
    while (( $# )); do
      case "$1" in -o|-g) shift 2 ;; *) args+=("$1"); shift ;; esac
    done
    exec /usr/bin/install "${args[@]}" ;;
esac
exit 0
'''
            for tool in ('id', 'sysctl', 'xcrun', 'xcode-select', 'lpstat', 'lpinfo', 'osascript', 'install',
                         'chown', 'launchctl', 'lpadmin', 'cupsaccept', 'cupsreject', 'cupsenable', 'cupsdisable', 'cupstestppd', 'cancel', 'lp'):
                write_script(mock / tool, common)
            paths = ('/Library/Printers/hp1020', '/Library/LaunchDaemons/', '/private/var/spool/cups/tmp/hp1020queue',
                     '/private/etc/cups/ppd/', '/usr/libexec/cups/backend/', '/usr/libexec/cups/filter/', '/opt/homebrew')
            for src in INPUTS:
                dst = repo / src.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                if src.suffix in ('.sh', '.in', '.ppd', '.h'):
                    text = dst.read_text()
                    for path in paths:
                        text = text.replace(path, str(target) + path)
                    text = text.replace('export PATH=/usr/bin:/bin:/usr/sbin:/sbin', f'export PATH="{mock}:{SYSTEM_PATH}"')
                    dst.write_text(text)
            write_script(target / 'usr/libexec/cups/backend/usb', '''#!/bin/zsh
print -r -- "$DEVICE_URI $*" >> "$MOCK_USB_CALLS"
exit "${MOCK_USB_EXIT:-0}"
''')
            return {'area': area, 'target': target, 'repo': repo, 'home': home, 'prefix': prefix,
                    'state': state, 'env': env, 'base': target / 'Library/Printers/hp1020',
                    'record': home / '.local/state/hp1020'}

        def action(f, name, ok=True, **extra):
            return command(['/bin/zsh', f['repo'] / 'scripts' / f'{name}.sh'], env=dict(f['env'], **extra), ok=ok)
        def packages(f):
            return set(json.loads(f['state'].read_text())['formulae'])
        def add_packages(f, *names):
            data = json.loads(f['state'].read_text())
            data['formulae'] = sorted(set(data['formulae']) | set(names))
            f['state'].write_text(json.dumps(data))

        f = fixture('fresh', existing=False)
        for extra in ({'MOCK_ARM64':'0'},{'MOCK_NO_CLT':'1'},{'MOCK_DEVICE':'none'},{'MOCK_PENDING':'1'},{'MOCK_UID':'0'}):
            assert action(f,'install',ok=False,**extra).returncode
            assert not f['prefix'].exists() and not f['base'].exists()
        passed('preflight rejects unsupported platform, missing tools/device, pending jobs and sudo before changes')
        action(f,'install')
        assert not f['prefix'].exists() and not f['record'].exists()
        assert (f['base']/'runtime/rastertohp1020').exists()
        assert not (f['base']/'hp1020-service.py').exists()
        assert not (f['target']/'Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist').exists()
        command([f['base']/'hp1020-print','-n','4','-p','Letter',pdf],env=f['env'])
        calls=Path(f['env']['MOCK_CALLS']).read_text()
        assert 'lp -d HP_LaserJet_1020_Plus -n 4 -o PageSize=Letter -o Collate=True -- ' in calls
        assert 'curl ' not in calls and 'brew ' not in calls and 'launchctl bootstrap' not in calls
        assert not Path(f['env']['MOCK_USB_CALLS']).exists()
        assert command([f['base']/'hp1020-print',test/'absent.pdf'],env=f['env'],ok=False).returncode
        action(f,'uninstall'); action(f,'uninstall')
        assert not f['base'].exists() and not f['prefix'].exists()
        passed('fresh native install/uninstall needs no packages, private queue or daemon; helper submits through CUPS')

        f=fixture('protected-source')
        action(f,'install',MOCK_REPO_HIDDEN='1')
        assert (f['base']/'runtime/rastertohp1020').exists()
        action(f,'uninstall')
        passed('elevated installation uses staged input with the repository inaccessible')

        def owned(f,names,created=False):
            f['record'].mkdir(parents=True,exist_ok=True)
            (f['record']/'formulae').write_text('\n'.join(sorted(names))+'\n')
            if created: (f['record']/'created-homebrew').touch()

        f=fixture('pre-existing',('ghostscript','gnu-sed','python@3.14','fontlib','pydep','orphan'))
        action(f,'install'); action(f,'install'); action(f,'uninstall')
        assert packages(f)=={'ghostscript','gnu-sed','python@3.14','fontlib','pydep','orphan'}
        passed('pre-existing Homebrew packages survive installation, reinstallation and removal')

        old_packages={'ghostscript','gnu-sed','python@3.14','fontlib','pydep'}
        f=fixture('legacy-migration',old_packages)
        owned(f,old_packages,True)
        f['base'].mkdir(parents=True)
        (f['base']/'hp1020-service.py').write_text('old service')
        (f['base']/'runtime').mkdir(); (f['base']/'runtime/old-worker').touch()
        for name in ('usr/libexec/cups/backend/hp1020queue','usr/libexec/cups/filter/hp1020passthrough','usr/libexec/cups/filter/hp1020zjs','Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist'):
            (f['target']/name).write_text('legacy component')
        Path(f['env']['MOCK_QUEUE']).touch(); Path(f['env']['MOCK_URI']).write_text('hp1020queue://localhost')
        Path(f['env']['MOCK_QUEUE_PPD']).write_text('old PPD')
        assert action(f,'install',ok=False,MOCK_COPY_FAIL='1').returncode
        assert (f['base']/'hp1020-service.py').read_text()=='old service'
        assert Path(f['env']['MOCK_URI']).read_text().strip()=='hp1020queue://localhost'
        assert packages(f)==old_packages
        action(f,'install')
        assert not (f['base']/'hp1020-service.py').exists() and not (f['base']/'runtime/old-worker').exists()
        assert not (f['target']/'usr/libexec/cups/filter/hp1020zjs').exists()
        assert not packages(f) and not f['prefix'].exists() and not f['record'].exists()
        assert Path(f['env']['MOCK_URI']).read_text().startswith('hp1020://Hewlett-Packard/')
        passed('legacy migration rolls back completely on failure, then removes old worker/files and only owned packages')

        f=fixture('shared',old_packages|{'other-app','orphan'})
        owned(f,old_packages,True); action(f,'install'); action(f,'uninstall')
        assert packages(f)=={'other-app','fontlib','orphan'} and f['prefix'].exists()
        passed('cleanup preserves dependencies now used by other software and its Homebrew installation')

        f=fixture('interrupted',('orphan','fontlib','unrelated'))
        f['record'].mkdir(parents=True)
        (f['record']/'before').write_text('orphan\n')
        (f['record']/'expected').write_text('fontlib\nghostscript\ngnu-sed\n')
        action(f,'uninstall')
        assert packages(f)=={'orphan','unrelated'}
        passed('interrupted old package bookkeeping recovers without claiming unrelated packages')

        f=fixture('retry',old_packages); owned(f,old_packages)
        action(f,'install',MOCK_UNINSTALL_FAIL='1')
        assert f['record'].exists() and (f['base']/'runtime/rastertohp1020').exists()
        action(f,'install'); assert not packages(f) and not f['record'].exists()
        passed('package cleanup failure retains its record and working native driver for retry')

        f=fixture('cask-query-failure',old_packages); owned(f,old_packages,True)
        assert action(f,'uninstall',ok=False,MOCK_CASK_QUERY_FAIL='1').returncode
        assert f['record'].exists() and f['prefix'].exists()
        action(f,'uninstall'); assert not f['record'].exists() and not f['prefix'].exists()
        passed('failed package inventory preserves Homebrew and cleanup record until successful retry')

        f=fixture('admin-cancel',existing=False)
        assert action(f,'install',ok=False,MOCK_ADMIN_FAIL='1').returncode
        assert not f['base'].exists() and not f['prefix'].exists()
        passed('cancelled administrator authorization leaves no installed driver or added dependencies')

        f=fixture('rollback')
        action(f,'install')
        queue_ppd=Path(f['env']['MOCK_QUEUE_PPD'])
        queue_ppd.write_text(queue_ppd.read_text()+'*% Local queue setting\n')
        saved_ppd=queue_ppd.read_bytes(); saved_uri=Path(f['env']['MOCK_URI']).read_text()
        saved={p.relative_to(f['base']):p.read_bytes() for p in f['base'].rglob('*') if p.is_file()}
        for variable in ('MOCK_COPY_FAIL','MOCK_LPADMIN_FAIL','MOCK_HEALTH_FAIL','MOCK_FATAL_EXPANSION','MOCK_ENABLE_FAIL','MOCK_ACCEPT_FAIL'):
            Path(f['env']['MOCK_LAUNCH_MARKER']).unlink(missing_ok=True)
            assert action(f,'install',ok=False,**{variable:'1'}).returncode
            assert all((f['base']/n).read_bytes()==content for n,content in saved.items())
            assert queue_ppd.read_bytes()==saved_ppd and Path(f['env']['MOCK_URI']).read_text()==saved_uri
            assert Path(f['env']['MOCK_ACCEPTED']).exists()
        Path(f['env']['MOCK_ACCEPTED']).unlink()
        Path(f['env']['MOCK_ENABLED']).unlink()
        Path(f['env']['MOCK_LAUNCH_MARKER']).unlink(missing_ok=True)
        assert action(f,'install',ok=False,MOCK_ACCEPT_FAIL='1').returncode
        assert not Path(f['env']['MOCK_ACCEPTED']).exists() and not Path(f['env']['MOCK_ENABLED']).exists()
        passed('copy, queue, health, fatal-shell and final enable/accept failures restore files, URI, PPD and disabled/rejecting state')

        calls=Path(f['env']['MOCK_CALLS']).read_text()
        assert action(f,'install',ok=False,MOCK_PENDING_ADMIN='1').returncode
        new=Path(f['env']['MOCK_CALLS']).read_text()[len(calls):]
        assert 'install -m ' not in new and 'launchctl bootout' not in new
        passed('job arriving during build prevents installed changes')
        queue=f['target']/'private/var/spool/cups/tmp/hp1020queue'; queue.mkdir(parents=True)
        for name in ('old-job','.incoming.unfinished'):
            (queue/name).write_text('pending legacy job')
            assert action(f,'install',ok=False).returncode and (queue/name).exists()
            (queue/name).unlink()
        passed('visible and hidden legacy pending jobs block migration without deleting documents')
        assert action(f,'uninstall',ok=False,MOCK_QUEUE_REMOVE_FAIL='1').returncode
        assert (f['base']/'runtime/rastertohp1020').exists()
        action(f,'uninstall')
        passed('failed queue removal preserves installed driver until cleanup can be retried')
        assert not (ROOT/'UNEXPECTED').exists()

    sources = INPUTS + [Path(__file__)]
    report = {'checks': checks, 'count': len(checks), 'conversion_cases': conversions,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'host_macos': command(['/usr/bin/sw_vers', '-productVersion']).stdout.decode().strip(),
              'runtime_dependencies': 'macOS only',
              'actual_installation': False, 'actual_homebrew_changes': False, 'printer_contact': False,
              'physical_print_test': False, 'fresh_mac_installation': False}
    (ROOT / 'assets/macos-setup-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Passed {len(checks)} offline checks. No actual installation, Homebrew changes or printer contact.')


if __name__ == '__main__':
    main()
