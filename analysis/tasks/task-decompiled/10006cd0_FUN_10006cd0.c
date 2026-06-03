/* Function: 10006cd0 FUN_10006cd0 */


/* WARNING: Control flow encountered bad instruction data */

void FUN_10006cd0(void)

{
  uint uVar1;
  uint uVar2;
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
  wsr(in_INTCLEAR,DAT_10005ccc);
  wsr(in_EPC2,0);
  wsr(in_EPS2,0);
  wsr(in_EXCSAVE2,0);
  wsr(in_DDR,0);
  uVar1 = 0;
  uVar2 = DAT_10005cd0;
  do {
    if (uVar1 == (DAT_10005cd4 & DAT_10005ca0)) {
      witlb(uVar1,uVar2 & 0xf);
      isync();
      if (uVar1 == DAT_10005ca0) goto LAB_10006d84;
    }
    else {
      witlb(uVar1,uVar2 & 0xf);
      if (uVar1 == DAT_10005ca0) {
        isync();
LAB_10006d84:
        uVar2 = DAT_10005cd0;
        for (uVar1 = 0; wdtlb(uVar1,uVar2 & 0xf), uVar1 != DAT_10005ca0;
            uVar1 = uVar1 - DAT_10005ca0) {
          uVar2 = uVar2 >> 4;
        }
        dsync();
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
    }
    uVar2 = uVar2 >> 4;
    uVar1 = uVar1 - DAT_10005ca0;
  } while( true );
}


