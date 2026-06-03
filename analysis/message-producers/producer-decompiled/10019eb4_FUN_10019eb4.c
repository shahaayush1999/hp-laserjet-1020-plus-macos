/* Function: 10019eb4 FUN_10019eb4 */


undefined4 FUN_10019eb4(int param_1,undefined4 *param_2,int param_3)

{
  undefined *puVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  int iVar5;
  undefined4 *puVar6;
  undefined4 uVar7;
  undefined4 *puVar8;
  undefined4 uVar9;
  
  puVar1 = PTR_LAB_10006b84;
  uVar9 = rsil(1);
  if (*(int *)(param_1 + 0x10) == 0) {
    if (param_3 != 0) {
      iVar2 = *(int *)PTR_DAT_10006a9c;
      *(int *)(iVar2 + 0x6c) = param_1;
      *(undefined4 **)(iVar2 + 0x7c) = param_2;
      *(undefined **)(iVar2 + 0x68) = puVar1;
      if (*(int *)(param_1 + 0x28) == 0) {
        *(int *)(param_1 + 0x28) = iVar2;
        *(int *)(iVar2 + 0x70) = iVar2;
        *(int *)(iVar2 + 0x74) = iVar2;
      }
      else {
        *(int *)(iVar2 + 0x70) = *(int *)(param_1 + 0x28);
        *(undefined4 *)(iVar2 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x28) + 0x74);
        *(int *)(*(int *)(*(int *)(param_1 + 0x28) + 0x74) + 0x70) = iVar2;
        *(int *)(*(int *)(param_1 + 0x28) + 0x74) = iVar2;
      }
      puVar1 = PTR_DAT_10006ac0;
      *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + 1;
      *(undefined4 *)(iVar2 + 0x30) = 5;
      *(undefined4 *)(iVar2 + 0x38) = 1;
      iVar5 = *(int *)puVar1;
      *(int *)(iVar2 + 0x4c) = param_3;
      *(int *)puVar1 = iVar5 + 1;
      wsr(0,uVar9);
      rsync();
      if (param_3 != -1) {
        FUN_1001a590(iVar2 + 0x4c);
      }
      FUN_100176c8(iVar2);
      return *(undefined4 *)(iVar2 + 0x84);
    }
    uVar7 = 10;
    goto LAB_1001a124;
  }
  uVar3 = *(uint *)(param_1 + 8);
  puVar6 = *(undefined4 **)(param_1 + 0x20);
  if (uVar3 == 2) {
LAB_10019f4c:
    *param_2 = *puVar6;
    puVar6 = puVar6 + 1;
    param_2 = param_2 + 1;
  }
  else {
    if (2 < uVar3) {
      if (uVar3 != 4) {
        if (uVar3 != 8) goto LAB_10019edc;
        goto LAB_10019f1c;
      }
LAB_10019f3c:
      *param_2 = *puVar6;
      param_2[1] = puVar6[1];
      puVar6 = puVar6 + 2;
      param_2 = param_2 + 2;
      goto LAB_10019f4c;
    }
    if (uVar3 != 1) {
LAB_10019edc:
      *param_2 = *puVar6;
      param_2[1] = puVar6[1];
      param_2[2] = puVar6[2];
      param_2[3] = puVar6[3];
      param_2[4] = puVar6[4];
      param_2[5] = puVar6[5];
      param_2[6] = puVar6[6];
      param_2[7] = puVar6[7];
      puVar6 = puVar6 + 8;
      param_2 = param_2 + 8;
LAB_10019f1c:
      *param_2 = *puVar6;
      param_2[1] = puVar6[1];
      param_2[2] = puVar6[2];
      param_2[3] = puVar6[3];
      puVar6 = puVar6 + 4;
      param_2 = param_2 + 4;
      goto LAB_10019f3c;
    }
  }
  *param_2 = *puVar6;
  uVar3 = *(int *)(param_1 + 8) * 4 + *(int *)(param_1 + 0x20);
  *(uint *)(param_1 + 0x20) = uVar3;
  if (*(uint *)(param_1 + 0x1c) <= uVar3) {
    *(undefined4 *)(param_1 + 0x20) = *(undefined4 *)(param_1 + 0x18);
  }
  puVar1 = PTR_DAT_10006ac0;
  uVar7 = 0;
  if (*(int *)(param_1 + 0x28) == 0) {
    *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + 1;
    *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + -1;
LAB_1001a124:
    wsr(0,uVar9);
    rsync();
    return uVar7;
  }
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
  wsr(0,uVar9);
  rsync();
  uVar9 = rsil(1);
  iVar2 = *(int *)(param_1 + 0x28);
  puVar6 = *(undefined4 **)(param_1 + 0x24);
  uVar3 = *(uint *)(param_1 + 8);
  puVar8 = *(undefined4 **)(iVar2 + 0x7c);
  *(int *)puVar1 = *(int *)puVar1 + -1;
  if (uVar3 != 2) {
    if (uVar3 < 3) {
      if (uVar3 == 1) goto LAB_1001a031;
LAB_10019fb9:
      *puVar6 = *puVar8;
      puVar6[1] = puVar8[1];
      puVar6[2] = puVar8[2];
      puVar6[3] = puVar8[3];
      puVar6[4] = puVar8[4];
      puVar6[5] = puVar8[5];
      puVar6[6] = puVar8[6];
      puVar6[7] = puVar8[7];
      puVar8 = puVar8 + 8;
      puVar6 = puVar6 + 8;
LAB_10019ff9:
      *puVar6 = *puVar8;
      puVar6[1] = puVar8[1];
      puVar6[2] = puVar8[2];
      puVar6[3] = puVar8[3];
      puVar8 = puVar8 + 4;
      puVar6 = puVar6 + 4;
    }
    else if (uVar3 != 4) {
      if (uVar3 != 8) goto LAB_10019fb9;
      goto LAB_10019ff9;
    }
    *puVar6 = *puVar8;
    puVar6[1] = puVar8[1];
    puVar8 = puVar8 + 2;
    puVar6 = puVar6 + 2;
  }
  *puVar6 = *puVar8;
  puVar8 = puVar8 + 1;
  puVar6 = puVar6 + 1;
LAB_1001a031:
  *puVar6 = *puVar8;
  uVar4 = *(int *)(param_1 + 8) * 4 + *(int *)(param_1 + 0x24);
  *(uint *)(param_1 + 0x24) = uVar4;
  if (*(uint *)(param_1 + 0x1c) <= uVar4) {
    *(undefined4 *)(param_1 + 0x24) = *(undefined4 *)(param_1 + 0x18);
  }
  if (iVar2 == *(int *)(iVar2 + 0x70)) {
    *(undefined4 *)(param_1 + 0x28) = 0;
  }
  else {
    *(int *)(param_1 + 0x28) = *(int *)(iVar2 + 0x70);
    *(undefined4 *)(*(int *)(iVar2 + 0x70) + 0x74) = *(undefined4 *)(iVar2 + 0x74);
    *(undefined4 *)(*(int *)(iVar2 + 0x74) + 0x70) = *(undefined4 *)(iVar2 + 0x70);
  }
  puVar1 = PTR_DAT_10006ac0;
  *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + -1;
  iVar5 = *(int *)puVar1;
  *(undefined4 *)(iVar2 + 0x68) = 0;
  *(int *)puVar1 = iVar5 + 1;
  wsr(0,uVar9);
  rsync();
  if (*(int *)(iVar2 + 100) == 0) {
    *(undefined4 *)(iVar2 + 0x4c) = 0;
  }
  else {
    FUN_1001bac4(iVar2 + 0x4c,uVar3,uVar9);
  }
  *(undefined4 *)(iVar2 + 0x84) = 0;
  iVar2 = FUN_1001aac0(iVar2);
  if (iVar2 != 0) {
    FUN_10018750();
  }
  return 0;
}


