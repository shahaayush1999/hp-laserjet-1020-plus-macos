/* Function: 10100020 hp1020_reset_vector_candidate */


/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void hp1020_reset_vector_candidate(void)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  int iVar4;
  uint uVar5;
  uint uVar6;
  undefined1 in_LBEG;
  undefined1 in_LEND;
  undefined1 in_LCOUNT;
  undefined1 in_WindowBase;
  undefined1 in_WindowStart;
  undefined1 in_DDR;
  undefined1 in_IBREAKA0;
  undefined1 in_IBREAKA1;
  undefined1 in_DBREAKA0;
  undefined1 in_DBREAKA1;
  undefined1 in_DBREAKC0;
  undefined1 in_DBREAKC1;
  undefined1 in_EPC1;
  undefined1 in_EPC2;
  undefined1 in_EPS2;
  undefined1 in_EXCSAVE1;
  undefined1 in_EXCSAVE2;
  undefined1 in_INTCLEAR;
  undefined1 in_INTENABLE;
  undefined1 in_EXCCAUSE;
  undefined1 in_CCOUNT;
  undefined1 in_ICOUNTLEVEL;
  undefined1 in_CCOMPARE0;
  
  puVar3 = _UNK_1010003c;
  uVar2 = _UNK_10100030;
  puVar1 = _UNK_1010002c;
  wsr(in_INTENABLE,0);
  wsr(in_CCOUNT,0);
  wsr(in_WindowBase,0);
  rsync();
  wsr(in_WindowStart,1);
  rsync();
  wsr(in_LCOUNT,0);
  wsr(in_LBEG,0);
  wsr(in_LEND,0);
  wsr(in_ICOUNTLEVEL,0);
  isync();
  wsr(in_DBREAKC0,0);
  wsr(in_DBREAKA0,0);
  wsr(in_DBREAKC1,0);
  wsr(in_DBREAKA1,0);
  wsr(in_IBREAKA0,0);
  wsr(in_IBREAKA1,0);
  wsr(0,1);
  rsync();
  wsr(in_EPC1,0);
  wsr(in_EXCSAVE1,0);
  wsr(in_EXCCAUSE,0);
  wsr(in_CCOMPARE0,0);
  wsr(in_INTCLEAR,_UNK_10100028);
  wsr(in_EPC2,0);
  wsr(in_EPS2,0);
  wsr(in_EXCSAVE2,0);
  wsr(in_DDR,0);
  *_UNK_10100034 = _UNK_10100038;
  *puVar3 = 0xd9;
  *puVar1 = uVar2;
  iVar4 = _UNK_10100040;
  do {
    iVar4 = iVar4 + -1;
  } while (iVar4 != 0);
  uVar5 = 0;
  uVar6 = _UNK_10100044;
  do {
    if (uVar5 == (_UNK_1010004c & _UNK_10100048)) {
      witlb(uVar5,uVar6 & 0xf);
      isync();
      if (uVar5 == _UNK_10100048) goto code_r0x10100144;
    }
    else {
      witlb(uVar5,uVar6 & 0xf);
      if (uVar5 == _UNK_10100048) {
        isync();
code_r0x10100144:
        uVar6 = _UNK_10100044;
        for (iVar4 = 0; wdtlb(iVar4,uVar6 & 0xf), iVar4 != _UNK_10100050;
            iVar4 = iVar4 - _UNK_10100050) {
          uVar6 = uVar6 >> 4;
        }
        dsync();
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
    }
    uVar6 = uVar6 >> 4;
    uVar5 = uVar5 - _UNK_10100048;
  } while( true );
}


