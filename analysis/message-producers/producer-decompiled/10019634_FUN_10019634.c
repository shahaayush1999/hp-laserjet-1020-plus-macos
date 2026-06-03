/* Function: 10019634 FUN_10019634 */


undefined4 FUN_10019634(int param_1,int param_2)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined4 uVar3;
  int iVar4;
  int iVar5;
  undefined4 uVar6;
  uint uVar7;
  
  puVar2 = PTR_LAB_10006b80;
  puVar1 = PTR_DAT_10006a9c;
  uVar6 = rsil(1);
  if (*(int *)(param_1 + 8) == 0) {
    *(undefined4 *)(param_1 + 8) = 1;
    iVar5 = *(int *)puVar1;
    *(int *)(param_1 + 0xc) = iVar5;
    if ((*(int *)(param_1 + 0x10) != 0) && (iVar5 != 0)) {
      *(undefined4 *)(param_1 + 0x14) = *(undefined4 *)(iVar5 + 0x2c);
      *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(iVar5 + 0x3c);
    }
  }
  else {
    iVar5 = *(int *)PTR_DAT_10006a9c;
    if (*(int *)(param_1 + 0xc) != iVar5) {
      if (param_2 != 0) {
        *(int *)(iVar5 + 0x6c) = param_1;
        *(undefined **)(iVar5 + 0x68) = puVar2;
        if (*(int *)(param_1 + 0x1c) == 0) {
          *(int *)(param_1 + 0x1c) = iVar5;
          *(int *)(iVar5 + 0x70) = iVar5;
          *(int *)(iVar5 + 0x74) = iVar5;
        }
        else {
          *(int *)(iVar5 + 0x70) = *(int *)(param_1 + 0x1c);
          *(undefined4 *)(iVar5 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x1c) + 0x74);
          *(int *)(*(int *)(*(int *)(param_1 + 0x1c) + 0x74) + 0x70) = iVar5;
          *(int *)(*(int *)(param_1 + 0x1c) + 0x74) = iVar5;
        }
        puVar1 = PTR_DAT_10006ac0;
        *(int *)(param_1 + 0x20) = *(int *)(param_1 + 0x20) + 1;
        *(undefined4 *)(iVar5 + 0x30) = 0xd;
        *(undefined4 *)(iVar5 + 0x38) = 1;
        iVar4 = *(int *)puVar1;
        *(int *)(iVar5 + 0x4c) = param_2;
        *(int *)puVar1 = iVar4 + 1;
        wsr(0,uVar6);
        rsync();
        if ((((*(int *)(param_1 + 0x10) != 0) && (iVar4 = *(int *)(param_1 + 0xc), iVar4 != 0)) &&
            (*(int *)PTR_DAT_10006a9c != 0)) &&
           (uVar7 = *(uint *)(*(int *)PTR_DAT_10006a9c + 0x2c), uVar7 < *(uint *)(iVar4 + 0x2c))) {
          FUN_10019860(iVar4,uVar7);
        }
        if (param_2 != -1) {
          FUN_1001a590(iVar5 + 0x4c);
        }
        FUN_100176c8(iVar5);
        return *(undefined4 *)(iVar5 + 0x84);
      }
      uVar3 = 0x1d;
      goto LAB_10019700;
    }
    *(int *)(param_1 + 8) = *(int *)(param_1 + 8) + 1;
  }
  uVar3 = 0;
LAB_10019700:
  wsr(0,uVar6);
  rsync();
  return uVar3;
}


