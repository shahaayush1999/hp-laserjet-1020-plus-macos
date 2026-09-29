#!/usr/bin/env python3
"""Compare stock USB bytes with pinned Synopsys UDC definitions, RAM only.

Register-family agreement is an inference, not silicon identification or a
working port. The selected original re-arm helper runs with one explicit
descriptor-submit literal redirected to a guarded RAM sink. Unmodified-MMIO
controls reject before the store in both engines. No controller is emulated.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct

from hp1020_xtensa_call0 import Program
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_stock_notifications import invoke
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_task import run_task

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/usb-path/controller-family'
REF = ROOT/'analysis/usb-path/controller-reference/linux-v6.12'
ENTRY, END, SUBMIT = 0x100086f4, 0x100087b8, 0x10008762
ARENA, DESCRIPTOR, SINK, BUFFER = 0x22000000, 0x22000100, 0x22000200, 0x22300000
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
REARM_SHA = '44aeebdd192f1f632caae561daba16438239e3cc12e8594af7ed6a8aeb7d9b84'
REV = 'adc218676eef25575469234709c2d87185ca223a'
REFERENCES = {
    'amd5536udc.h':'8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c':'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
    'snps_udc_plat.c':'25728c88031b8e19613d0b47708cef643635dd937d8a4bb3ab118500fbf2843d',
    'GPL-2.0':'f6b78c087c3ebdf0f3c13415070dd480a3f35d8fc76f3d02180a407c1c812f79',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

class RearmRAM(StopRAM):
    def __init__(self, program, fill, next_pointer, redirect=True):
        super().__init__(program, ENTRY, [(ENTRY,END)], [(ARENA,0x1000)])
        self.put(ARENA,bytes([fill])*0x1000)
        self.write(self.read(0x10005e2c,4),4,DESCRIPTOR)
        self.write(self.read(0x10005e44,4),4,BUFFER)
        self.write(self.read(0x10005e54,4),4,next_pointer)
        for at in (0x10005e28,0x10005e58,0x10005e20,0x10005e64):
            self.write(self.read(at,4),1,fill)
        if redirect:
            # Change this data literal only in the private RAM copy. Preserve
            # original instruction bytes and the on-disk stock ELF.
            assert self.read(0x10005e60,4)==0xb3000234
            self.write_ranges.append((0x10005e60,0x10005e64))
            self.write(0x10005e60,4,SINK)

    def observed(self):
        return dict(arena=self.bytes_at(ARENA,0x1000),
                    flags=[self.read(self.read(at,4),1)
                           for at in (0x10005e28,0x10005e58,0x10005e20,0x10005e64)])

def main():
    stock=ROOT/'analysis/sihp1020.elf'; blob=stock.read_bytes()
    assert sha(blob)==STOCK_SHA
    sections,_=properties(blob)
    raw=lambda at,n: section_bytes(blob,sections,at,n)
    word=lambda at: int.from_bytes(raw(at,4),'big')
    assert sha(raw(ENTRY,END-ENTRY))==REARM_SHA
    for name,digest in REFERENCES.items():
        assert sha((REF/name).read_bytes())==digest,(name,'reference hash changed')
    provenance=json.loads((REF/'provenance.json').read_text())
    assert provenance['commit']==REV
    assert {Path(i['path']).name for i in provenance['files']}==set(REFERENCES)
    for item in provenance['files']:
        name=Path(item['path']).name
        assert item['sha256']==REFERENCES[name]
        assert item['url']==f'https://raw.githubusercontent.com/torvalds/linux/{REV}/{item["path"]}'
        assert item['bytes']==(REF/name).stat().st_size
    header=(REF/'amd5536udc.h').read_text()
    definitions={name:int(value,0) for name,value in re.findall(
        r'^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$',header,re.M)}
    def members(name):
        body=re.search(r'struct '+name+r'\s*\{(.*?)\}',header,re.S).group(1)
        body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
        return re.findall(r'\bu32\s+(\w+)\s*;',body)
    assert members('udc_ep_regs')==['ctl','sts','bufin_framenum','bufout_maxpkt','subptr','desptr','reserved','confirm']
    assert members('udc_data_dma')==['status','_reserved','bufptr','next']
    stride=4*len(members('udc_ep_regs'))
    base=0xb3000000
    comparisons=[]
    def match(name,at,expected,upstream):
        value=word(at)
        assert value==expected,(name,hex(value),hex(expected))
        comparisons.append(dict(name=name,literal=hex(at),stock_value=hex(value),
            expected_value=hex(expected),upstream=upstream,status='match'))
    for at,key in ((0x10005df4,'DEVCFG'),(0x10005ea8,'DEVCTL'),(0x10005e68,'DEVSTS'),
                   (0x10005de4,'DEVINT'),(0x10005eb8,'DEVINT_MSK'),
                   (0x10005de8,'EPINT'),(0x10005e00,'EPINT_MSK')):
        macro='UDC_'+key+'_ADDR'; match(key.lower(),at,base+definitions[macro],[macro])
    for name,at,bank,ep,key in (
        ('in0_status',0x10005e04,'IN',0,'EPSTS'),('out0_status',0x10005e08,'OUT',0,'EPSTS'),
        ('out0_control',0x10005e24,'OUT',0,'EPCTL'),('out1_control',0x10005e70,'OUT',1,'EPCTL'),
        ('out1_max_packet',0x10005f08,'OUT',1,'EP_MAX_PKT_SIZE'),
        ('out1_descriptor',0x10005e60,'OUT',1,'EP_DESPTR'),
        ('in1_descriptor',0x10005e84,'IN',1,'EP_DESPTR'),
        ('in0_max_packet',0x10005e9c,'IN',0,'EP_MAX_PKT_SIZE'),
        ('in0_descriptor',0x10005ea0,'IN',0,'EP_DESPTR'),
        ('out0_setup',0x10005ef4,'OUT',0,'EP_SUBPTR'),
        ('out0_descriptor',0x10005ef8,'OUT',0,'EP_DESPTR'),
        ('out0_max_packet',0x10005ee4,'OUT',0,'EP_MAX_PKT_SIZE')):
        bank_macro='UDC_EP'+bank+'_REGS_ADDR'; offset_macro='UDC_'+key+'_ADDR'
        match(name,at,base+definitions[bank_macro]+ep*stride+definitions[offset_macro],
              [bank_macro,f'endpoint {ep} * sizeof(struct udc_ep_regs)',offset_macro])
    match('descriptor_owner_mask',0x10005e30,definitions['UDC_DMA_OUT_STS_BS_MASK'],['UDC_DMA_OUT_STS_BS_MASK'])
    match('descriptor_dma_done',0x10005e34,
          definitions['UDC_DMA_OUT_STS_BS_DMA_DONE']<<definitions['UDC_DMA_OUT_STS_BS_OFS'],
          ['UDC_DMA_OUT_STS_BS_DMA_DONE','UDC_DMA_OUT_STS_BS_OFS'])
    match('descriptor_last',0x10005e80,1<<definitions['UDC_DMA_OUT_STS_L'],['UDC_DMA_OUT_STS_L'])
    match('enumerated_speed_mask',0x10005ea4,definitions['UDC_DEVSTS_ENUM_SPEED_MASK'],['UDC_DEVSTS_ENUM_SPEED_MASK'])
    match('control_pair_and_out1_unmasked',0x10005f04,0xffffffff ^ (1<<definitions['UDC_EPINT_IN_EP0']) ^
          (1<<definitions['UDC_EPINT_OUT_EP0']) ^ (1<<definitions['UDC_EPINT_OUT_EP1']),
          ['UDC_EPINT_IN_EP0','UDC_EPINT_OUT_EP0','UDC_EPINT_OUT_EP1'])
    prefix=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program=Program(stock,prefix)
    instructions=[]
    def ins(at,encoding,op,args,meaning):
        actual=program.instruction(at)
        assert actual==(op,tuple(args),bytes.fromhex(encoding)),(hex(at),actual)
        instructions.append(dict(address=hex(at),bytes=encoding,opcode=op,operands=args,meaning=meaning))
    ins(0x100083e3,'0b5811','slli',[8,5,5],'Endpoint register stride is 1 << 5 bytes.')
    assert stride==1<<5
    ins(0x10008446,'284a00','movi',[8,1024],'Endpoint status mask 1 << UDC_EPSTS_TDC.')
    assert 1024==1<<definitions['UDC_EPSTS_TDC']
    ins(0x100084dd,'2a0a80','movi',[10,128],'Endpoint control mask 1 << UDC_EPCTL_SNAK.')
    assert 128==1<<definitions['UDC_EPCTL_SNAK']
    ins(0x10009031,'1af39d','l32r',[10,0x10005ea8],'Device control address for the following initialization branch.')
    ins(0x10009064,'293a20','movi',[9,800],'Initialization mask includes BE, burst-enable and DMA-mode bits in the reference.')
    ins(0x10009067,'098802','or',[8,8,9],'OR the supplied initialization mask into the device-control value.')
    ins(0x1000906d,'98a0','s32i.n',[8,10,0],'Static write-site audit only; this peripheral store is never executed.')
    assert 800==sum(1<<definitions['UDC_DEVCTL_'+name] for name in ('BE','BREN','MODE'))
    ins(0x10008522,'089901','and',[9,9,8],'Mask assembled descriptor word with original 0xc0000000 literal.')
    ins(0x10008525,'7a9102','beq',[9,10,0x1000852b],'Admit only original 0x80000000 owner state.')
    for at,encoding,op,args in ((0x10008536,'28b002','l8ui',[8,11,2]),
             (0x10008539,'29b003','l8ui',[9,11,3]),(0x1000853c,'088811','slli',[8,8,8]),
             (0x1000853f,'098702','or',[7,8,9])):
        ins(at,encoding,op,args,'Completed byte count is descriptor bytes 2/3, big endian.')
    assert definitions['UDC_DMA_OUT_STS_RXBYTES_MASK']==0xffff
    assert definitions['UDC_DMA_OUT_STS_RXBYTES_OFS']==0
    for at,encoding,op,args in ((0x1000877a,'c048','movi.n',[4,8]),
        (0x1000877f,'243400','s8i',[4,3,0]),(0x1000878b,'253401','s8i',[5,3,1]),
        (0x10008797,'253402','s8i',[5,3,2]),(0x100087a6,'253403','s8i',[5,3,3])):
        ins(at,encoding,op,args,'Re-arm writes status bytes 08 00 00 00 after its submission store.')
    assert (8<<24)==1<<definitions['UDC_DMA_OUT_STS_L']
    assert definitions['UDC_DMA_OUT_STS_BS_HOST_READY']==0
    for row in comparisons:
        at=int(row['literal'],16)
        row['load_sites']=[hex(pc) for pc,(op,args,_) in program.instructions.items() if op=='l32r' and args[1]==at]
        assert row['load_sites'],row['name']
    cases=[]; excluded=[]; decoded=[]
    with QemuRAM() as q:
        version=q.version
        for fill in (0,204):
            for offset in (0,37):
                for pointer in (0,0x22340567,0x22340560):
                    expected_pointer=pointer if pointer and not (pointer&15) else BUFFER+offset
                    expected=bytearray([fill]*0x1000)
                    expected[0x100:0x104]=struct.pack('>I',1<<definitions['UDC_DMA_OUT_STS_L'])
                    expected[0x108:0x110]=struct.pack('>II',expected_pointer,0)
                    expected[0x200:0x204]=struct.pack('>I',DESCRIPTOR)
                    flags=[int(bool(pointer) and not(pointer&15)),0,1,0]
                    observations=[]; steps=[]
                    for engine in (None,q):
                        state=RearmRAM(program,fill,pointer)
                        invoke(state,ENTRY,[offset],qemu=engine)
                        observed=state.observed()
                        assert observed['arena']==expected and observed['flags']==flags
                        observations.append(observed)
                        steps.append(state.qemu_steps if engine else state.steps)
                    assert observations[0]==observations[1]
                    cases.append(dict(status='pass',fill=fill,offset=offset,next_pointer=hex(pointer),
                        buffer_pointer=hex(expected_pointer),descriptor_hex=bytes(expected[0x100:0x110]).hex(),
                        arena_sha256=sha(bytes(expected)),flags=flags,interpreter_steps=steps[0],qemu_steps=steps[1],
                        entire_guarded_arena_equal=True))
        for engine in (None,q):
            state=RearmRAM(program,204,0,redirect=False)
            try:
                invoke(state,ENTRY,[37],qemu=engine)
            except ValueError as error:
                assert state.pc==SUBMIT,(state.pc,str(error))
                if engine: assert q.reg(0)==SUBMIT and str(error)=='MMIO forbidden'
                else: assert str(error)=='write outside mutable RAM 0xb3000234'
                excluded.append(dict(engine='QEMU' if engine else 'interpreter',status='rejected before execution',
                    pc=hex(SUBMIT),effective_address='0xb3000234',reason=str(error)))
            else: raise AssertionError('unredirected peripheral store was not rejected')
        # Pure-RAM status fragment, entered after the omitted IRQ/NAK prefix.
        # The next branch/store beyond each selected boundary is never stepped.
        vectors=[(owner,last,0,count) for owner in range(4) for last in (0,1)
                 for count in (0,1,64,512,1024,65535)]
        vectors += [(2,1,error,37) for error in (1,2,3)]
        for owner,last,receive_status,count in vectors:
            status=(owner<<30)|(last<<27)|(receive_status<<28)|count
            expected_done=owner==definitions['UDC_DMA_OUT_STS_BS_DMA_DONE']
            boundary=0x10008542 if expected_done else 0x1000867c
            results=[]
            for engine in (None,q):
                state=RearmRAM(program,204,0,redirect=False)
                state.code_ranges=[(0x100084f9,0x10008542)]
                state.pc=0x100084f9
                state.write(DESCRIPTOR,4,status)
                state.write(state.read(0x10005e38,4),4,0)
                before=state.bytes_at(ARENA,0x1000)
                try:
                    if engine: run_task(state,q,(),prologue=0x10008208)
                    else: state.run()
                except ValueError as error:
                    assert state.pc==boundary,(owner,last,receive_status,count,state.pc,str(error))
                    if engine:
                        assert q.reg(0)==boundary
                        assert str(error)==f'QEMU task left selected code: {boundary:#x}'
                        ar7=q.reg(((q.reg(38)*4+7)%32)+1)
                        assert q.read(ARENA,0x1000)==before
                    else:
                        assert str(error)==f'execution outside selected stock routines: {boundary:#x}'
                        ar7=state.registers[7]
                        assert state.bytes_at(ARENA,0x1000)==before
                else: raise AssertionError('status fragment crossed its selected boundary')
                observed_count=ar7 if expected_done else None
                if expected_done: assert observed_count==count
                results.append(observed_count)
            assert results[0]==results[1]
            decoded.append(dict(status='pass',descriptor_status=hex(status),owner=owner,last=last,
                receive_status=receive_status,encoded_count=count,owner_admitted=expected_done,
                decoded_count=results[0],stop=hex(boundary),guarded_arena_unchanged=True))
    sources=[Path(__file__),stock,REF/'provenance.json',*(REF/name for name in REFERENCES)]
    sources += [ROOT/'scripts'/name for name in (
        'hp1020_xtensa_call0.py','hp1020_xtensa_properties.py','hp1020_xtensa_stock.py',
        'hp1020_stock_stop.py','hp1020_stock_notifications.py','hp1020_qemu_ram.py',
        'hp1020_qemu_task.py','hp1020_qemu_stock_parser.py')]
    report=dict(status='pass',source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},
        upstream_commit=REV,comparisons=comparisons,instructions=instructions,rearm_sha256=REARM_SHA,
        qemu_version=version,rearm_cases=cases,excluded_controls=excluded,status_decoding_cases=decoded,
        inference='Strong register/descriptor-family match to the classic Synopsys device-only UDC used by the Linux snps_udc driver; not the DWC2 high-speed OTG register layout. This does not identify an AMD chip or prove a compatible silicon revision.',
        limits='Original re-arm construction executes with supplied globals and the submission literal redirected to RAM. Status decoding starts after the omitted IRQ/NAK prefix, with a supplied descriptor, and stops before either next path. No USB controller behavior, real DMA/interrupts/cache, setup/reset/cancel correctness, live traffic, boot or printing is established. HP-specific wrapper registers at 0xb3010000/4 remain outside this match. The Linux driver is a reference, not a linked runtime or usable HP port.',
        completed_native_page_lifecycles=0)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    url=f'https://github.com/torvalds/linux/blob/{REV}/drivers/usb/gadget/udc/'
    lines=['# USB controller-family comparison','',report['inference'],'',
        f'Pinned Linux v6.12 [register definitions]({url}amd5536udc.h), [driver]({url}snps_udc_core.c) and [platform glue]({url}snps_udc_plat.c) are preserved with provenance and GPL license under `controller-reference/linux-v6.12/`.','',
        f'{len(comparisons)} stock literal/layout matches and {len(instructions)} byte-checked instruction anchors. Twelve re-arm cases agree between original instruction interpretation, independent QEMU and an independently constructed byte oracle. Both unredirected-store controls reject before MMIO.','',
        '| Item | Stock literal | Value |','|---|---|---|']
    lines += [f'| {c["name"]} | `{c["literal"]}` | `{c["stock_value"]}` |' for c in comparisons]
    lines += ['',
        'The old re-arm note called the leading byte an opcode/value 8. The full status word is `0x08000000`: the reference identifies bit 27 as the last-descriptor flag, with ownership bits 31:30 zero (host ready). Stock completion separately requires ownership 2 and reads the low 16-bit count. These labels are a cross-source interpretation supported by exact original bytes, not live controller observation.','',
        'Re-arm preserves descriptor bytes 4..7, selects an aligned nonzero next pointer or base plus offset, writes the target at +8, and clears +12. Submission precedes the status-byte stores in the original instruction order; this RAM experiment does not validate the bus ordering. Entire guard regions and completion flags are compared under two initial fills.','',
        f'{len(decoded)} separate original RAM-fragment cases cross all four ownership states, both last-flag values and counts 0/1/64/512/1024/65535. Both engines admit only owner state 2 and reconstruct the low 16-bit count. Three additional receive-status controls show that this fragment does not reject bits 29:28: they must not be promoted to valid-transfer evidence. Zero is only the decoded field value here, not proof of how a real zero-length or 65536-byte transfer is represented. The IRQ/NAK prefix and downstream update/re-arm paths remain excluded.','',
        'A separately byte-checked startup branch ORs `0x320` into device control, matching the reference BE/burst/mode bit positions. The branch and its peripheral stores are inspected only. This supports investigating the controller byte-order setting; it does not prove live configuration or portable DMA/cache behavior.','',
        'Use the existing Linux controller code to guide a small freestanding adapter, then assess a generic USB/printer class layer. Retain HP-specific startup, byte order, cache/alias and reset/abort questions. Do not add peripheral writes to the current software image pipeline or bypass the existing inert hardware-test ladder.','',report['limits'],'']
    OUT.with_suffix('.md').write_text('\n'.join(lines))
    print(f'USB controller family: {len(comparisons)} byte-derived matches, {len(cases)} dual-engine re-arm cases, {len(decoded)} status fragments, {len(excluded)} pre-MMIO rejections')

if __name__=='__main__':
    main()
