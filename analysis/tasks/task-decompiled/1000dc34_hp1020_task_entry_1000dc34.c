/* Function: 1000dc34 hp1020_task_entry_1000dc34 */


undefined4 hp1020_task_entry_1000dc34(undefined4 param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  char cVar4;
  int iVar5;
  char acStack_30 [48];
  
  acStack_30[0] = '\x01';
  *(undefined4 *)PTR_DAT_100060bc = param_1;
  puVar2 = PTR_DAT_10006278;
  *(undefined4 *)PTR_DAT_10006290 = 0;
  *(undefined4 *)puVar2 = 0;
  FUN_1000ae94();
  iVar5 = *(int *)puVar2;
  *(undefined4 *)PTR_DAT_100060ac = *(undefined4 *)PTR_DAT_100060a8;
  puVar1 = PTR_DAT_1000626c;
  while (iVar5 == 0) {
    iVar5 = FUN_1000d700();
    iVar3 = 0;
    if ((acStack_30[0] != '\0') && (iVar5 != -4)) {
      acStack_30[0] = '\0';
    }
    switch(iVar5) {
    case -5:
      FUN_1000dd7c(6);
      *puVar1 = 1;
      goto LAB_1000dc97;
    case -4:
      cVar4 = FUN_1000dba8();
      if (cVar4 == '\0') {
        *(undefined4 *)puVar2 = 2;
        FUN_1000dda8();
      }
      else {
        FUN_1000dd40(acStack_30);
      }
LAB_1000dc97:
      iVar3 = 0;
      break;
    case -3:
      iVar3 = 0x12;
      break;
    case -2:
      iVar3 = FUN_1000d2a8();
      break;
    case -1:
      break;
    default:
      iVar3 = (**(code **)(PTR_PTR_100062a4 + iVar5 * 8 + 4))();
    }
    if ((iVar3 != 0) && (iVar3 != 6)) {
      FUN_1000dd7c(iVar3);
    }
    FUN_1000af88();
    if (*(int *)puVar2 != 0) break;
    while (*puVar1 == '\0') {
      FUN_1000d6b0();
      iVar5 = *(int *)PTR_DAT_10006270;
      if ((((iVar5 < 0x21) && (iVar5 != 0x20)) && (iVar5 != 9)) && (iVar5 != 10)) {
        if (iVar5 != -1) {
          FUN_1000dd60();
        }
        FUN_1000dd7c(6);
        *puVar1 = 1;
      }
    }
    FUN_1000af88();
    iVar5 = *(int *)puVar2;
  }
  *PTR_DAT_10006280 = 1;
  FUN_1000ddc0();
  return 0;
}


