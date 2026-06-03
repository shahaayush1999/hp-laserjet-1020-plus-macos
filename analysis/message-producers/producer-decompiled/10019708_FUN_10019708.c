/* Function: 10019708 FUN_10019708 */


undefined4 FUN_10019708(int param_1,undefined4 param_2,int param_3,int param_4)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  undefined1 uVar5;
  undefined1 uVar6;
  
  uVar6 = 0;
  uVar4 = rsil(1);
  if ((*(int *)(param_1 + 8) == 0) || (*(int *)(param_1 + 0xc) != *(int *)PTR_DAT_10006a9c)) {
    wsr(0,uVar4);
    rsync();
    return 0x1e;
  }
  iVar2 = *(int *)(param_1 + 8) + -1;
  *(int *)(param_1 + 8) = iVar2;
  puVar1 = PTR_DAT_10006ac0;
  if (iVar2 != 0) {
    wsr(0,uVar4);
    rsync();
    return 0;
  }
  uVar5 = 0;
  if (*(int *)(param_1 + 0x10) != 0) {
    if (*(int *)(param_1 + 0x1c) == 0) goto LAB_1001975d;
    *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
    wsr(0,uVar4);
    rsync();
    uVar5 = 0;
    FUN_1001b918(param_1,uVar4);
    uVar4 = rsil(1);
    *(int *)puVar1 = *(int *)puVar1 + -1;
  }
  uVar6 = uVar5;
  iVar2 = *(int *)(param_1 + 0x1c);
  if (iVar2 != 0) {
    if (*(int *)(param_1 + 0x10) != 0) {
      param_3 = *(int *)(param_1 + 0x14);
      param_2 = *(undefined4 *)(param_1 + 0x18);
      *(undefined4 *)(param_1 + 0x14) = *(undefined4 *)(iVar2 + 0x2c);
      param_4 = *(int *)(param_1 + 0xc);
      *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(iVar2 + 0x3c);
    }
    *(undefined4 *)(param_1 + 8) = 1;
    *(int *)(param_1 + 0xc) = iVar2;
    if (iVar2 == *(int *)(iVar2 + 0x70)) {
      *(undefined4 *)(param_1 + 0x1c) = 0;
    }
    else {
      *(int *)(param_1 + 0x1c) = *(int *)(iVar2 + 0x70);
      *(undefined4 *)(*(int *)(iVar2 + 0x70) + 0x74) = *(undefined4 *)(iVar2 + 0x74);
      *(undefined4 *)(*(int *)(iVar2 + 0x74) + 0x70) = *(undefined4 *)(iVar2 + 0x70);
    }
    puVar1 = PTR_DAT_10006ac0;
    *(int *)(param_1 + 0x20) = *(int *)(param_1 + 0x20) + -1;
    iVar3 = *(int *)puVar1;
    *(undefined4 *)(iVar2 + 0x68) = 0;
    *(int *)puVar1 = iVar3 + 1;
    wsr(uVar6,uVar4);
    rsync();
    if (*(int *)(iVar2 + 100) == 0) {
      *(undefined4 *)(iVar2 + 0x4c) = 0;
    }
    else {
      FUN_1001bac4(iVar2 + 0x4c,uVar4);
    }
    *(undefined4 *)(iVar2 + 0x84) = 0;
    if (((*(int *)(param_1 + 0x10) != 0) && (param_4 != 0)) && (*(int *)(param_4 + 0x2c) != param_3)
       ) {
      FUN_10019860(param_4,param_3,param_2);
    }
    iVar2 = FUN_1001aac0(iVar2);
    if (iVar2 != 0) {
      FUN_10018750();
    }
    return 0;
  }
LAB_1001975d:
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
  wsr(uVar6,uVar4);
  rsync();
  if (((*(int *)(param_1 + 0x10) != 0) && (*(int *)PTR_DAT_10006a9c != 0)) &&
     (*(int *)(*(int *)PTR_DAT_10006a9c + 0x2c) != *(int *)(param_1 + 0x14))) {
    FUN_10019860(*(undefined4 *)(param_1 + 0xc),*(int *)(param_1 + 0x14),
                 *(undefined4 *)(param_1 + 0x18));
  }
  uVar4 = rsil(1);
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
  wsr(uVar6,uVar4);
  rsync();
  if ((*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) && (*(int *)PTR_DAT_10005d80 == 0)) {
    FUN_10018750(*(int *)PTR_DAT_10006a9c,uVar4);
  }
  return 0;
}


