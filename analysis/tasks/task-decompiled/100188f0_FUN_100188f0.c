/* Function: 100188f0 FUN_100188f0 */


undefined1  [16] FUN_100188f0(void)

{
  int iVar2;
  undefined1 auVar1 [16];
  undefined1 in_LBEG;
  undefined1 in_LEND;
  undefined1 in_LCOUNT;
  undefined1 in_SAR;
  undefined1 in_EPC1;
  
  wsr(0,DAT_10005c98);
  rsync();
  do {
    iVar2 = *(int *)PTR_DAT_10006aa0;
  } while (iVar2 == 0);
  wsr(0,0x21);
  rsync();
  *(int *)PTR_DAT_10006a9c = iVar2;
  *(int *)(iVar2 + 4) = *(int *)(iVar2 + 4) + 1;
  *(undefined4 *)PTR_DAT_10006ac8 = *(undefined4 *)(iVar2 + 0x18);
  iVar2 = *(int *)(iVar2 + 8);
  wsr(0,*(undefined4 *)(iVar2 + 0x50));
  rsync();
  wsr(in_EPC1,*(undefined4 *)(iVar2 + 0x54));
  wsr(in_SAR,*(undefined4 *)(iVar2 + 0x4c));
  wsr(in_LBEG,*(undefined4 *)(iVar2 + 0x40));
  wsr(in_LEND,*(undefined4 *)(iVar2 + 0x44));
  wsr(in_LCOUNT,*(undefined4 *)(iVar2 + 0x48));
  rfe();
  auVar1._8_4_ = *(undefined4 *)(iVar2 + 0xc);
  auVar1._12_4_ = *(undefined4 *)(iVar2 + 8);
  auVar1._4_4_ = *(undefined4 *)(iVar2 + 0x10);
  auVar1._0_4_ = *(undefined4 *)(iVar2 + 0x14);
  return auVar1;
}


