#!/usr/bin/env python3
"""Test repository setup with isolated Homebrew, admin, CUPS and USB fixtures.

Never runs real package-manager mutations, installation or printer commands.
Python is for maintainers/tests only; end users run the two zsh scripts.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
INPUTS = [*(ROOT / "templates").glob("*.in"), *(ROOT / "assets/runtime").glob("*"),
          ROOT / "assets/licenses/foo2zjs-COPYING", ROOT / "files/cups/backend/hp1020queue",
          ROOT / "files/cups/filter/hp1020passthrough", ROOT / "files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd",
          *(ROOT / "scripts" / name for name in ("install.sh", "uninstall.sh", "macos-common.sh",
             "rebuild-runtime-from-vendor.sh", "diagnose.sh", "print-test.sh")),
          *(ROOT / "vendor/foo2zjs-source" / name for name in ("foo2zjs.c", "zjs.h", "jbig.c", "jbig.h", "jbig_ar.c", "jbig_ar.h"))]

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
deps = {'ghostscript': {'fontlib'}, 'gnu-sed': set(), 'fontlib': set(), 'other-app': {'fontlib'}, 'unrelated': set(), 'orphan': set()}
cmd = args[0]
if cmd == '--prefix': print(os.environ['MOCK_PREFIX'])
elif cmd == 'list':
    if os.environ.get('MOCK_QUERY_FAIL') == '1': sys.exit(7)
    if '--cask' in args and os.environ.get('MOCK_CASK_QUERY_FAIL') == '1': sys.exit(7)
    print('\\n'.join(sorted(data.get('casks', []) if '--cask' in args else installed)))
elif cmd == 'deps': print('fontlib')
elif cmd == 'install':
    installed.add('fontlib')
    if os.environ.get('MOCK_INSTALL_FAIL') != '1':
        installed.update(a for a in args[1:] if not a.startswith('-'))
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
        # Compile only the encoder; render with the already-installed Homebrew tools.
        runtime = test / 'runtime with spaces'
        command(['/bin/zsh', ROOT / 'scripts/rebuild-runtime-from-vendor.sh', runtime], env=clean)
        command(['/usr/bin/codesign', '--verify', '--strict', runtime / 'foo2zjs'])
        assert command(['/usr/bin/lipo', '-archs', runtime / 'foo2zjs']).stdout.strip() == b'arm64'
        ps = test / 'sample with spaces.ps'
        ps.write_text('%!PS-Adobe-3.0\n%%Pages: 2\n/Helvetica findfont 18 scalefont setfont\n'
                      '72 720 moveto (Homebrew printer setup) show\n0.3 setgray 72 400 100 90 rectfill showpage\n'
                      '0 setgray 100 300 75 0 360 arc stroke showpage\n%%EOF\n')
        pdf = test / 'sample with spaces.pdf'
        gs, gsed = Path('/opt/homebrew/bin/gs'), Path('/opt/homebrew/bin/gsed')
        command([gs, '-q', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite', f'-sOutputFile={pdf}', ps], env=clean)
        env = dict(clean, PATH=f'{runtime}:/opt/homebrew/bin:{SYSTEM_PATH}', GSBIN='gs')
        reference_env = dict(env, PATH=f'{ROOT / "assets/runtime"}:/opt/homebrew/bin:{SYSTEM_PATH}')
        for document in (ps, pdf):
            for code, copies in (('9', '1'), ('1', '2')):
                opts = ['-P', '-z1', '-L0', '-p' + code, '-n' + copies]
                actual = command([runtime / 'foo2zjs-wrapper', *opts, document], env=env).stdout
                original = command([ROOT / 'assets/runtime/foo2zjs-wrapper', *opts], env=reference_env, data=document.read_bytes()).stdout
                assert stream(actual) == stream(original)
                conversions.append({'format': document.suffix, 'paper_code': code, 'copies': copies,
                                    'original_chunks_match': True, 'sha256': hashlib.sha256(actual).hexdigest()})
        passed('native encoder build and four PDF/PostScript conversions match every original encoder chunk')
        invalid = test / 'invalid.pdf'
        invalid.write_bytes(b'%PDF-1.7\nbroken\n')
        assert command([runtime / 'foo2zjs-wrapper', '-P', '-z1', invalid], env=env, ok=False).returncode
        passed('invalid document conversion fails')

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
                       MOCK_PREFIX=str(prefix), MOCK_CALLS=str(area / 'calls'), MOCK_USB_CALLS=str(area / 'usb-calls'))
            brew_template = write_script(area / 'brew-template', MOCK_BREW.replace('PYTHON', sys.executable, 1))
            bootstrap = write_script(area / 'bootstrap.py', f'''#!{sys.executable}
import os, pathlib, shutil, sys
prefix = pathlib.Path(os.environ['MOCK_PREFIX'])
if sys.argv[1] == 'install':
    (prefix / 'bin').mkdir(parents=True, exist_ok=True)
    shutil.copy2({str(brew_template)!r}, prefix / 'bin/brew')
    for name, source in [('gs', {str(gs)!r}), ('gsed', {str(gsed)!r})]:
        (prefix / 'bin' / name).symlink_to(source)
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
  lpstat) [[ "${MOCK_PENDING:-0}" != 1 ]] || print 'HP_LaserJet_1020_Plus-1 dad 100' ;;
  lpinfo) [[ "${MOCK_DEVICE:-one}" == one ]] && print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=FAMILY "HP"'; exit 0 ;;
  osascript) [[ "${MOCK_ADMIN_FAIL:-0}" != 1 ]] || exit 1; exec /bin/zsh "$argv[-1]" ;;
  install)
    args=()
    while (( $# )); do
      case "$1" in -o|-g) shift 2 ;; *) args+=("$1"); shift ;; esac
    done
    exec /usr/bin/install "${args[@]}" ;;
esac
exit 0
'''
            for tool in ('id', 'sysctl', 'xcrun', 'xcode-select', 'lpstat', 'lpinfo', 'osascript', 'install',
                         'chown', 'launchctl', 'lpadmin', 'cupsaccept', 'cupsenable', 'cancel'):
                write_script(mock / tool, common)
            paths = ('/Library/Printers/hp1020', '/Library/LaunchDaemons/', '/private/var/spool/cups/tmp/hp1020queue',
                     '/private/etc/cups/ppd/', '/usr/libexec/cups/backend/', '/usr/libexec/cups/filter/', '/opt/homebrew')
            for src in INPUTS:
                dst = repo / src.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                if src.suffix in ('.sh', '.in') or src.name in ('hp1020queue', 'hp1020passthrough'):
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
        for extra in ({'MOCK_ARM64': '0'}, {'MOCK_NO_CLT': '1'}, {'MOCK_DEVICE': 'none'}, {'MOCK_PENDING': '1'}, {'MOCK_UID': '0'}):
            assert action(f, 'install', ok=False, **extra).returncode
            assert not f['prefix'].exists() and not f['base'].exists()
        passed('preflight rejects wrong platform, missing build tools/device, pending jobs and sudo invocation before package changes')
        action(f, 'install')
        assert packages(f) == {'ghostscript', 'gnu-sed', 'fontlib'}
        assert set((f['record'] / 'formulae').read_text().splitlines()) == packages(f)
        assert (f['record'] / 'created-homebrew').exists()
        command([f['base'] / 'hp1020-print', pdf], env=f['env'])
        assert len(Path(f['env']['MOCK_USB_CALLS']).read_text().splitlines()) == 2
        before = Path(f['env']['MOCK_USB_CALLS']).read_bytes()
        assert command([f['base'] / 'hp1020-print', invalid], env=f['env'], ok=False).returncode
        assert Path(f['env']['MOCK_USB_CALLS']).read_bytes() == before
        action(f, 'uninstall')
        action(f, 'uninstall')
        assert not f['base'].exists() and not f['prefix'].exists() and not f['record'].exists()
        assert not packages(f)
        passed('fresh setup bootstraps official Homebrew URLs, renders before mock USB, then removes its packages/Homebrew repeatably')

        f = fixture('existing', ('ghostscript', 'fontlib', 'orphan'))
        action(f, 'install')
        assert (f['record'] / 'formulae').read_text().splitlines() == ['gnu-sed']
        action(f, 'uninstall')
        assert packages(f) == {'ghostscript', 'fontlib', 'orphan'} and f['prefix'].exists()
        passed('pre-existing Homebrew, requested packages and unrelated orphan dependencies are preserved')

        f = fixture('shared', ('orphan',))
        action(f, 'install')
        add_packages(f, 'other-app')
        action(f, 'uninstall')
        assert packages(f) == {'other-app', 'fontlib', 'orphan'}
        passed('newly shared dependencies are preserved for other software')

        f = fixture('reinstall', existing=False)
        action(f, 'install')
        add_packages(f, 'unrelated')
        action(f, 'install')
        assert 'unrelated' not in (f['record'] / 'formulae').read_text().splitlines()
        action(f, 'uninstall')
        assert packages(f) == {'unrelated'} and f['prefix'].exists()
        passed('reinstallation keeps original ownership; Homebrew is retained when later used for other software')

        f = fixture('partial', ('orphan',))
        assert action(f, 'install', ok=False, MOCK_INSTALL_FAIL='1').returncode
        assert not f['base'].exists() and (f['record'] / 'formulae').read_text().splitlines() == ['fontlib']
        action(f, 'uninstall')
        assert packages(f) == {'orphan'}
        passed('partially failed dependency installation remains removable')

        f = fixture('interrupted', ('orphan', 'fontlib', 'unrelated'))
        f['record'].mkdir(parents=True)
        (f['record'] / 'before').write_text('orphan\n')
        (f['record'] / 'expected').write_text('fontlib\nghostscript\ngnu-sed\n')
        action(f, 'uninstall')
        assert packages(f) == {'orphan', 'unrelated'}
        passed('interrupted package bookkeeping recovers without claiming unrelated later installs')

        f = fixture('retry', ())
        action(f, 'install')
        assert action(f, 'uninstall', ok=False, MOCK_UNINSTALL_FAIL='1').returncode
        assert f['record'].exists()
        action(f, 'uninstall')
        assert not packages(f) and not f['record'].exists()
        passed('failed cleanup retains its ownership record and succeeds on retry')

        f = fixture('cask-query-failure', existing=False)
        action(f, 'install')
        assert action(f, 'uninstall', ok=False, MOCK_CASK_QUERY_FAIL='1').returncode
        assert f['record'].exists() and f['prefix'].exists()
        action(f, 'uninstall')
        assert not f['record'].exists() and not f['prefix'].exists()
        passed('failed cask inventory keeps Homebrew and its cleanup record until a successful retry')

        f = fixture('admin-cancel', existing=False)
        assert action(f, 'install', ok=False, MOCK_ADMIN_FAIL='1').returncode
        assert not f['base'].exists()
        action(f, 'uninstall')
        assert not packages(f) and not f['prefix'].exists()
        passed('cancelled administrative installation can still undo the added dependencies')

    sources = INPUTS + [Path(__file__)]
    report = {'checks': checks, 'count': len(checks), 'conversion_cases': conversions,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'host_macos': command(['/usr/bin/sw_vers', '-productVersion']).stdout.decode().strip(),
              'renderer_version': command(['/opt/homebrew/bin/gs', '--version']).stdout.decode().strip(),
              'actual_installation': False, 'actual_homebrew_changes': False, 'printer_contact': False,
              'physical_print_test': False, 'fresh_mac_installation': False}
    (ROOT / 'assets/macos-setup-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Passed {len(checks)} offline checks. No actual installation, Homebrew changes or printer contact.')


if __name__ == '__main__':
    main()
