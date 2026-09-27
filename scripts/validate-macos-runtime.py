#!/usr/bin/env python3
"""Offline checks of the bundled runtime and simulated install/remove workflow.

System paths are relocated into a temporary tree. Service, administrator and USB
commands are mocked before any installer, worker or print helper is executed.
No installed files, CUPS configuration or physical device are accessed.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import stat
import struct
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("runtime_builder", ROOT / "scripts/build-macos-runtime.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"

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


def raster_difference(left, right):
    def raster(path):
        with path.open("rb") as image:
            magic = image.readline().strip()
            assert magic in (b"P4", b"P5")
            line = image.readline()
            while line.startswith(b"#"):
                line = image.readline()
            dimensions = list(map(int, line.split()))
            width, height = dimensions[:2]
            if magic == b"P5":
                assert dimensions[2:] == [3]  # foo2zjs -z1 pairs two PBM bits.
            pixels = image.read()
        stride = width if magic == b"P5" else (width + 7) // 8
        assert len(pixels) == stride * height
        return magic, width, height, pixels
    magic, width, height, a = raster(left)
    magic2, w2, h2, b = raster(right)
    assert (magic, width, height) == (magic2, w2, h2)
    stride = width if magic == b"P5" else (width + 7) // 8
    changed = []
    for index, (x, y) in enumerate(zip(a, b)):
        xor = x ^ y
        if xor:
            if magic == b"P5":
                changed.append((index % stride, index // stride))
            else:
                changed.extend(((index % stride) * 8 + bit, index // stride)
                               for bit in range(8) if xor & (128 >> bit))
    def edge(pixels, x, y):
        values = {pixels[yy * stride + xx] if magic == b"P5" else bool(pixels[yy * stride + xx // 8] & (128 >> (xx % 8)))
                  for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)}
        return len(values) > 1
    for x, y in changed:
        # Only the fixture's headings occupy these rows. Filled gray rectangle,
        # circle, whitespace, geometry and glyph interiors must remain identical.
        assert 0 < x < width - 1 and 0 < y < min(1400, height - 1)
        assert edge(a, x, y) and edge(b, x, y), (x, y)
    return {"width": width, "height": height, "different_pixels": len(changed),
            "classification": "single-pixel text edges" if changed else "identical",
            "difference_bounds": [min(x for x, y in changed), min(y for x, y in changed),
                                  max(x for x, y in changed), max(y for x, y in changed)] if changed else None}


def main():
    checks, cases, differences = [], [], []
    def passed(name):
        checks.append(name)
        print(f"PASS: {name}", flush=True)

    runtime = builder.OUTPUT
    info = json.loads((runtime / "build-info.json").read_text())
    builder.sources(builder.SOURCES)
    for archive_name, members in (
        ('ghostpdl-10.07.0.tar.xz', [('ghostpdl-10.07.0/LICENSE', 'Ghostscript-LICENSE.txt'),
                                  ('ghostpdl-10.07.0/doc/COPYING', 'Ghostscript-AGPL-3.0.txt')]),
        ('sed-4.10.tar.xz', [('sed-4.10/COPYING', 'GNU-sed-GPL-3.0.txt')]),
    ):
        with tarfile.open(builder.SOURCES / archive_name) as archive:
            for member, filename in members:
                assert archive.extractfile(member).read() == (ROOT / 'assets/licenses' / filename).read_bytes()
    assert info['recipe']['builder_sha256'] == builder.digest(ROOT / 'scripts/build-macos-runtime.py')
    for name, expected in info['binaries'].items():
        assert builder.binary_audit(runtime / name) == expected
    for relative, expected in {**info['original_inputs'], **info['recipe']['foo2zjs']}.items():
        assert builder.digest(ROOT / relative) == expected, relative
    assert (runtime / 'foo2zjs-wrapper').read_text() == builder.patched_wrapper()
    assert (runtime / 'sihp1020.dl').read_bytes() == (ROOT / 'assets/runtime/sihp1020.dl').read_bytes()
    command(['/usr/bin/shasum', '-a', '256', '-c', runtime / 'SHA256SUMS'],
            env=dict(os.environ, PWD=str(ROOT)))  # caller cwd is set below
    passed('pinned sources/licenses, generated wrapper, original firmware, signatures, arm64/macOS 11 target and system-only libraries')
    for path in [*(ROOT / 'scripts').glob('*install.sh'), ROOT / 'scripts/macos-common.sh',
                 ROOT / 'scripts/rebuild-runtime-from-vendor.sh', ROOT / 'scripts/diagnose.sh', ROOT / 'scripts/print-test.sh',
                 * (ROOT / 'templates').glob('*.in'),
                 ROOT / 'files/cups/backend/hp1020queue', ROOT / 'files/cups/filter/hp1020passthrough',
                 runtime / 'foo2zjs-wrapper', runtime / 'foo2zjs-pstops']:
        if path.read_bytes().startswith(b'#!'):
            command([path.read_text().splitlines()[0][2:], '-n', path])
    passed('shell syntax')

    with tempfile.TemporaryDirectory(prefix='hp1020-runtime-check-') as temporary:
        test = Path(temporary)
        clean = {'PATH': SYSTEM_PATH, 'LC_ALL': 'C', 'TMPDIR': str(test), 'HOME': str(test), 'USER': 'fixture'}
        ps = test / 'sample with spaces.ps'
        ps.write_text('%!PS-Adobe-3.0\n%%Pages: 2\n'
                      '/Helvetica findfont 20 scalefont setfont\n'
                      '72 720 moveto (HP 1020 portable package) show\n'
                      '0.3 setgray 72 500 240 90 rectfill showpage\n'
                      '0 setgray /Times-Roman findfont 16 scalefont setfont\n'
                      '72 700 moveto (Second page: 1234567890) show\n'
                      '100 300 75 0 360 arc stroke showpage\n%%EOF\n')
        pdf = test / 'sample with spaces.pdf'
        command([runtime / 'gs', '-q', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite', f'-sOutputFile={pdf}', ps], env=clean)
        actual_env = dict(clean, PATH=f'{runtime}:{SYSTEM_PATH}', GSBIN='gs')
        reference_env = dict(clean, PATH=f'{ROOT / "assets/runtime"}:{runtime}:{SYSTEM_PATH}', GSBIN='gs')
        for document in (ps, pdf):
            for paper, code, copies in (('a4', '9', '1'), ('letter', '1', '2')):
                options = ['-P', '-z1', '-L0', f'-p{code}', f'-n{copies}']
                actual = command([runtime / 'foo2zjs-wrapper', *options, document], env=actual_env).stdout
                reference = command([ROOT / 'assets/runtime/foo2zjs-wrapper', *options],
                                    env=reference_env, data=document.read_bytes()).stdout
                actual_chunks, reference_chunks = stream(actual), stream(reference)
                assert actual_chunks == reference_chunks
                pages = [items for kind, items, _ in actual_chunks if kind == 2]
                assert len(pages) == 2
                converted = test / f'{document.suffix[1:]}-{paper}.zjs'
                converted.write_bytes(actual)
                cases.append({'format': document.suffix, 'paper': paper, 'copies': int(copies), 'pages': len(pages),
                              'compressed_chunks_identical_to_original_encoder': True,
                              'output_sha256': hashlib.sha256(actual).hexdigest()})
        passed('four two-page PDF/PostScript conversions with system-only PATH; every ZjStream chunk matches the original encoder')

        # Compare the working renderer too, when it exists; do not make it a build/install requirement.
        brew_gs = Path('/opt/homebrew/bin/gs')
        if brew_gs.is_file():
            source = ROOT / 'vendor/foo2zjs-source'
            decoder = test / 'zjsdecode'
            command(['/usr/bin/clang', '-O2', '-I', source, '-o', decoder,
                     source / 'zjsdecode.c', source / 'jbig.c', source / 'jbig_ar.c'])
            for document in (ps, pdf):
                old = command([ROOT / 'assets/runtime/foo2zjs-wrapper', '-P', '-z1', '-L0', '-p9'],
                              env=dict(reference_env, GSBIN=str(brew_gs)), data=document.read_bytes()).stdout
                new_path = test / f'{document.suffix[1:]}-a4.zjs'
                left, right = stream(new_path.read_bytes()), stream(old)
                assert [(k, i) for k, i, _ in left] == [(k, i) for k, i, _ in right]
                assert [body for k, _, body in left if k != 5] == [body for k, _, body in right if k != 5]
                old_path = test / f'old-{document.suffix[1:]}.zjs'
                old_path.write_bytes(old)
                new_prefix, old_prefix = test / f'new-{document.suffix[1:]}', test / f'old-{document.suffix[1:]}'
                command([decoder, '-d', new_prefix, new_path])
                command([decoder, '-d', old_prefix, old_path])
                new_pages = sorted(test.glob(new_prefix.name + '-*.p?m'))
                old_pages = sorted(test.glob(old_prefix.name + '-*.p?m'))
                assert len(new_pages) == len(old_pages) == 2
                differences.extend(dict(format=document.suffix, page=index + 1, **raster_difference(a, b))
                                   for index, (a, b) in enumerate(zip(new_pages, old_pages)))
            passed('comparison with working Homebrew renderer: geometry/non-image chunks exact; measured raster changes restricted to text edges')

        invalid = test / 'broken.pdf'
        invalid.write_bytes(b'%PDF-1.7\nnot a valid PDF\n')
        assert command([runtime / 'foo2zjs-wrapper', '-P', '-z1', '-L0', '-p9', invalid], env=actual_env, ok=False).returncode
        passed('renderer errors propagate through the conversion pipeline')

        target, mock = test / 'target', test / 'mock-bin'
        repo = test / "Dad's repo $(touch UNEXPECTED) & files"
        user_home = target / "Users/Dad's home $(touch UNEXPECTED)"
        user_home.mkdir(parents=True)
        for directory in ('usr/libexec/cups/backend', 'usr/libexec/cups/filter',
                          'Library/LaunchDaemons', 'private/etc/cups/ppd'):
            (target / directory).mkdir(parents=True)
        calls = test / 'commands.txt'
        env = dict(clean, HP1020_HOME=str(user_home), HP1020_USER='dad', MOCK_CALLS=str(calls),
                   MOCK_USB_CALLS=str(test / 'usb-calls'))
        mock.mkdir()
        mock_common = '''#!/bin/zsh
print -r -- "${0:t} $*" >> "$MOCK_CALLS"
case "${0:t}" in
  sysctl) print "${MOCK_ARM64:-1}" ;;
  lpstat) [[ "${MOCK_PENDING:-0}" != 1 ]] || print 'HP_LaserJet_1020_Plus-1 dad 100' ;;
  lpinfo)
    case "${MOCK_DEVICE:-one}" in
      one) print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=FAMILY "HP"' ;;
      two) print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=ONE "HP"'; print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=TWO "HP"' ;;
      error) exit 2 ;;
    esac ;;
  osascript) exec /bin/zsh "$argv[-1]" ;;
  install)
    args=()
    while (( $# )); do
      case "$1" in
        -o|-g) shift 2 ;;
        *) args+=("$1"); shift ;;
      esac
    done
    exec /usr/bin/install "${args[@]}" ;;
  brew|curl|wget) exit 99 ;;
esac
exit 0
'''
        for name in ('sysctl', 'lpstat', 'lpinfo', 'osascript', 'install', 'chown', 'launchctl',
                     'lpadmin', 'cupsaccept', 'cupsenable', 'cancel', 'brew', 'curl', 'wget'):
            write_script(mock / name, mock_common)
        system_paths = ('/Library/Printers/hp1020', '/Library/LaunchDaemons/',
                        '/private/var/spool/cups/tmp/hp1020queue', '/private/etc/cups/ppd/',
                        '/usr/libexec/cups/backend/', '/usr/libexec/cups/filter/')
        for path in builder.installation_inputs() + [runtime / 'SHA256SUMS']:
            dest = repo / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            if path.suffix in ('.sh', '.in') or path.name in ('hp1020queue', 'hp1020passthrough'):
                text = dest.read_text()
                for absolute in system_paths:
                    text = text.replace(absolute, str(target) + absolute)
                text = text.replace('export PATH=/usr/bin:/bin:/usr/sbin:/sbin',
                                    f'export PATH="{mock}:{SYSTEM_PATH}"')
                # Shorten only the simulated document transfer deadline.
                text = text.replace('run_with_timeout 60 ', 'run_with_timeout 1 ')
                scrubbed = text.replace(str(target), '')
                assert text.count(str(target)) == sum(scrubbed.count(p) for p in system_paths)
                dest.write_text(text)
        # The fixture is intentionally relocated. Hash its changed scripts separately.
        fixture_sums = repo / 'assets/macos-arm64/SHA256SUMS'
        fixture_sums.write_text(''.join(f'{builder.digest(repo / p.relative_to(ROOT))}  {p.relative_to(ROOT)}\n'
                                       for p in builder.installation_inputs()))
        quarantined = [repo / 'assets/macos-arm64' / name for name in
                       ('gs', 'gsed', 'foo2zjs', 'foo2zjs-wrapper', 'foo2zjs-pstops')]
        quarantined += [repo / 'files/cups/backend/hp1020queue', repo / 'files/cups/filter/hp1020passthrough',
                        *(repo / 'scripts').glob('*.sh'), *(repo / 'templates').glob('*.in')]
        for path in quarantined:
            command(['/usr/bin/xattr', '-w', 'com.apple.quarantine', '0083;65000000;Safari;', path])
        install, remove = repo / 'scripts/install.sh', repo / 'scripts/uninstall.sh'
        base = target / 'Library/Printers/hp1020'
        usb = target / 'usr/libexec/cups/backend/usb'
        write_script(usb, '''#!/bin/zsh
print -r -- "$DEVICE_URI $# $*" >> "$MOCK_USB_CALLS"
[[ "$1" != 2 ]] || {
  [[ "${MOCK_USB_HANG:-0}" != 1 ]] || exec /bin/sleep 20
  exit "${MOCK_USB_EXIT:-0}"
}
''')
        for overrides in ({'MOCK_ARM64': '0'}, {'MOCK_DEVICE': 'none'}, {'MOCK_DEVICE': 'two'},
                          {'MOCK_DEVICE': 'error'}, {'MOCK_PENDING': '1'}):
            assert command(['/bin/zsh', install], env=dict(env, **overrides), ok=False).returncode
            assert not base.exists()
        included_sed = repo / 'assets/macos-arm64/gsed'
        original_sed = included_sed.read_bytes()
        included_sed.write_bytes(original_sed + b'corrupted')
        assert command(['/bin/zsh', install], env=env, ok=False).returncode
        included_sed.write_bytes(original_sed)
        assert not calls.exists() or 'osascript ' not in calls.read_text()
        passed('installation rejects Intel, missing/ambiguous devices, pending jobs and changed runtime bytes before administrative changes')

        legacy = user_home / '.local/share/hp1020'
        legacy.mkdir(parents=True)
        (legacy / 'old-runtime').write_text('old')
        legacy_helper = user_home / 'bin/hp1020-print'
        write_script(legacy_helper, '#!/bin/sh\nexit 99\n')
        unrelated = target / 'Library/Printers/Unrelated/keep'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('untouched')
        external = target / 'opt/homebrew/bin/gs'
        external.parent.mkdir(parents=True)
        external.write_text('not ours')
        command(['/bin/zsh', install], env=env)
        command(['/bin/zsh', install], env=env)
        assert not legacy.exists() and not legacy_helper.exists()
        assert unrelated.read_text() == 'untouched' and external.read_text() == 'not ours'
        for name in ('gs', 'gsed', 'foo2zjs', 'foo2zjs-wrapper', 'foo2zjs-pstops', 'sihp1020.dl'):
            assert builder.digest(base / 'runtime' / name) == builder.digest(runtime / name)
            assert 'com.apple.quarantine' not in command(['/usr/bin/xattr', base / 'runtime' / name]).stdout.decode()
        for license in (ROOT / 'assets/licenses').iterdir():
            assert (base / 'Licenses' / license.name).read_bytes() == license.read_bytes()
        plist = target / 'Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist'
        parsed = plistlib.loads(plist.read_bytes())
        assert parsed['ProgramArguments'] == [str(base / 'hp1020-root-spool-worker')]
        for path in (base / 'hp1020-print', base / 'hp1020-root-spool-worker',
                     target / 'usr/libexec/cups/backend/hp1020queue', target / 'usr/libexec/cups/filter/hp1020passthrough'):
            assert 'com.apple.quarantine' not in command(['/usr/bin/xattr', path]).stdout.decode()
        assert '-o printer-is-shared=false' in calls.read_text()
        assert not Path(env['MOCK_USB_CALLS']).exists()
        assert not (test / 'UNEXPECTED').exists() and not (ROOT / 'UNEXPECTED').exists()
        passed('simulated installation/reinstallation from quarantined payload, legacy removal and quoting for spaces/apostrophes/metacharacters')

        helper = base / 'hp1020-print'
        usb_calls = Path(env['MOCK_USB_CALLS'])
        command([helper, pdf], env=env)
        records = usb_calls.read_text().splitlines()
        assert len(records) == 2 and 'serial=FAMILY 6 1 ' in records[0] and 'serial=FAMILY 6 2 ' in records[1]
        usb_calls.unlink()
        assert command([helper, invalid], env=env, ok=False).returncode
        assert not usb_calls.exists()
        assert command([helper, '-p', 'invalid', ps], env=env, ok=False).returncode
        assert not usb_calls.exists()
        assert command([helper, '--no-firmware', ps], env=dict(env, MOCK_USB_EXIT='9'), ok=False).returncode == 9
        assert command([helper, '--no-firmware', ps], env=dict(env, MOCK_USB_HANG='1'), ok=False).returncode == 124
        passed('mock USB transfers only after conversion; invalid inputs, transfer errors and timeouts are not reported as success')

        backend = target / 'usr/libexec/cups/backend/hp1020queue'
        worker = base / 'hp1020-root-spool-worker'
        queue = target / 'private/var/spool/cups/tmp/hp1020queue'
        proc = subprocess.Popen([str(backend), '17', 'dad', 'sample title', '1', 'PageSize=A4'],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        try:
            proc.stdin.write(ps.read_bytes()[:50])
            proc.stdin.flush()
            for _ in range(100):
                if list(queue.glob('.incoming.*')):
                    break
                time.sleep(0.02)
            assert list(queue.glob('.incoming.*')) and not [p for p in queue.iterdir() if not p.name.startswith('.')]
            command([worker], env=env)
            assert not list((base / 'done').iterdir())
            proc.stdin.write(ps.read_bytes()[50:])
            proc.stdin.close()
            assert proc.wait(timeout=10) == 0
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        command([worker], env=env)
        done = list((base / 'done').iterdir())
        assert len(done) == 1 and done[0].read_bytes() == ps.read_bytes()
        before = usb_calls.read_bytes()
        command([backend, '18', 'dad', 'invalid', '1', 'PageSize=A4', invalid], env=env)
        command([worker], env=env)
        failed = list((base / 'failed').iterdir())
        assert len(failed) == 1 and failed[0].read_bytes() == invalid.read_bytes()
        command([worker], env=env)
        assert usb_calls.read_bytes() == before
        passed('queued documents become visible only when complete; worker records success/failure without retrying failed input')

        # Removal is independent of the bundled executables and device availability.
        included_sed.unlink()
        command(['/bin/zsh', remove], env=dict(env, MOCK_DEVICE='none'))
        command(['/bin/zsh', remove], env=dict(env, MOCK_DEVICE='none'))
        assert not base.exists() and not queue.exists() and not plist.exists()
        assert not backend.exists() and not (target / 'usr/libexec/cups/filter/hp1020passthrough').exists()
        assert unrelated.read_text() == 'untouched' and external.read_text() == 'not ours'
        assert usb_calls.read_bytes() == before
        assert not any(line.split()[0] in ('brew', 'curl', 'wget') for line in calls.read_text().splitlines())
        passed('simulated removal is repeatable, needs no device or working runtime, and preserves unrelated printers/Homebrew')

    report = {'checks': checks, 'count': len(checks), 'conversion_cases': cases, 'renderer_differences': differences,
              'source_sha256': {str(p.relative_to(ROOT)): builder.digest(p)
                                for p in builder.installation_inputs() + [Path(__file__), runtime / 'SHA256SUMS']},
              'host_macos': command(['/usr/bin/sw_vers', '-productVersion']).stdout.decode().strip(),
              'actual_installation': False, 'printer_contact': False, 'physical_print_test': False,
              'older_macos_execution': False, 'zip_download_gatekeeper_test': False,
              'quarantined_payload_simulation': True,
              'scope': 'mocked CUPS/admin/USB; A4 default queue path; wrapper also exercises Letter and two copies'}
    (ROOT / 'assets/macos-runtime-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Passed {len(checks)} offline checks. No real installation or printer contact.')


if __name__ == '__main__':
    os.chdir(ROOT)
    main()
