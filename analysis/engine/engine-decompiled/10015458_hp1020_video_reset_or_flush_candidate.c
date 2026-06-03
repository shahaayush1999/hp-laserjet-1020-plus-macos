/* Function: 10015458 hp1020_video_reset_or_flush_candidate */


undefined4 hp1020_video_reset_or_flush_candidate(void)

{
  undefined *puVar1;
  uint *puVar2;
  uint *puVar3;
  undefined4 uVar4;
  uint uVar5;
  undefined1 uVar6;
  
  puVar2 = DAT_100067c0;
  uVar4 = rsil(1);
  memw();
  memw();
  *DAT_10006808 = *DAT_10006808 & 0xfffffeff;
  puVar3 = DAT_1000680c;
  memw();
  uVar5 = *puVar2;
  while ((uVar5 & 0x200) != 0) {
    memw();
    uVar5 = *puVar2;
  }
  memw();
  memw();
  *DAT_10006808 = *DAT_10006808 | 0x100;
  puVar2 = DAT_100067d8;
  memw();
  memw();
  *puVar3 = *puVar3 & 0xfffffeff;
  memw();
  uVar5 = *puVar2;
  while ((uVar5 & 0x200) != 0) {
    memw();
    uVar5 = *puVar2;
  }
  if (*(int *)PTR_DAT_100067c8 == 1) {
    memw();
    memw();
    *DAT_1000680c = *DAT_1000680c | 0x100;
  }
  uVar6 = 0;
  FUN_10013d4c(1);
  puVar1 = PTR_DAT_10006770;
  if (*(int *)(PTR_DAT_10006770 + 0x70) == 1) {
    FUN_10018214(PTR_DAT_10006810);
    *(undefined4 *)(puVar1 + 0x70) = 0;
  }
  wsr(uVar6,uVar4);
  rsync();
  return 0;
}


