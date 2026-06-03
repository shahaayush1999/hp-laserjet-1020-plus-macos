/* Function: 10016d6f FUN_10016d6f */


void FUN_10016d6f(undefined4 param_1)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  undefined1 in_INTSET;
  undefined1 in_INTENABLE;
  
  wsr(0,DAT_10006a5c);
  rsync();
  uVar3 = rsr(in_INTSET);
  do {
    uVar2 = rsr(in_INTENABLE);
    uVar2 = uVar2 & uVar3;
    if (uVar2 == 0) {
      *(int *)PTR_DAT_10006a68 = *(int *)PTR_DAT_10006a68 + 1;
      break;
    }
    uVar3 = 0x1f - LZCOUNT(-uVar2 & uVar2);
    (**(code **)(PTR_PTR_10006a60 + uVar3 * 4))(uVar3);
    param_1 = 0xffffffff;
    uVar1 = 1 << 0x20 - (0x20 - (uVar3 & 0x1f)) ^ 0xffffffff;
    uVar3 = uVar2 & uVar1;
  } while ((uVar3 & uVar1) != 0);
  *(undefined4 *)PTR_DAT_10006a44 = 0xffffffff;
  (*(code *)PTR_FUN_10006a64)(param_1,PTR_FUN_10006a64);
  return;
}


