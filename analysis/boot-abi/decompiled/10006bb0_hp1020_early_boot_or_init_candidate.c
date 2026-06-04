/* Function: 10006bb0 hp1020_early_boot_or_init_candidate */


/* WARNING: Control flow encountered bad instruction data */

void hp1020_early_boot_or_init_candidate(void)

{
  undefined *puVar1;
  uint uVar2;
  undefined4 *puVar3;
  uint uVar4;
  undefined1 in_LCOUNT;
  undefined1 in_WindowBase;
  undefined1 in_WindowStart;
  
  puVar1 = PTR_DAT_10005ca8;
  wsr(in_LCOUNT,0);
  wsr(in_WindowStart,1);
  wsr(in_WindowBase,0);
  rsync();
  wsr(0,DAT_10005c98);
  rsync();
  uVar2 = 0;
  uVar4 = DAT_10005c9c;
  do {
    if (uVar2 == (DAT_10005ca4 & DAT_10005ca0)) {
      witlb(uVar2,uVar4 & 0xf);
      isync();
      if (uVar2 == DAT_10005ca0) goto LAB_10006c44;
    }
    else {
      witlb(uVar2,uVar4 & 0xf);
      if (uVar2 == DAT_10005ca0) {
        isync();
LAB_10006c44:
        uVar4 = DAT_10005c9c;
        for (uVar2 = 0; wdtlb(uVar2,uVar4 & 0xf), uVar2 != DAT_10005ca0;
            uVar2 = uVar2 - DAT_10005ca0) {
          uVar4 = uVar4 >> 4;
        }
        dsync();
        uVar4 = DAT_10005cac - (int)PTR_DAT_10005ca8;
        puVar3 = (undefined4 *)PTR_DAT_10005ca8;
        if ((uVar4 & 4) != 0) {
          *(undefined4 *)PTR_DAT_10005ca8 = 0;
          puVar3 = (undefined4 *)(puVar1 + 4);
          uVar4 = uVar4 - 4;
        }
        if ((uVar4 & 8) != 0) {
          *puVar3 = 0;
          puVar3[1] = 0;
        }
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
    }
    uVar4 = uVar4 >> 4;
    uVar2 = uVar2 - DAT_10005ca0;
  } while( true );
}


