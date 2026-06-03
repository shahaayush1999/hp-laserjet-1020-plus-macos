/* Function: 1001a130 FUN_1001a130 */


undefined4 FUN_1001a130(int param_1,undefined4 *param_2,int param_3)

{
  undefined *puVar1;
  undefined4 uVar2;
  int iVar3;
  undefined4 *puVar4;
  int iVar5;
  uint uVar6;
  undefined4 uVar7;
  
  puVar1 = PTR_LAB_10006b84;
  uVar7 = rsil(1);
  if (*(int *)(param_1 + 0x14) == 0) {
    if (param_3 != 0) {
      iVar5 = *(int *)PTR_DAT_10006a9c;
      *(int *)(iVar5 + 0x6c) = param_1;
      *(undefined4 **)(iVar5 + 0x7c) = param_2;
      *(undefined **)(iVar5 + 0x68) = puVar1;
      if (*(int *)(param_1 + 0x28) == 0) {
        *(int *)(param_1 + 0x28) = iVar5;
        *(int *)(iVar5 + 0x70) = iVar5;
        *(int *)(iVar5 + 0x74) = iVar5;
      }
      else {
        *(int *)(iVar5 + 0x70) = *(int *)(param_1 + 0x28);
        *(undefined4 *)(iVar5 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x28) + 0x74);
        *(int *)(*(int *)(*(int *)(param_1 + 0x28) + 0x74) + 0x70) = iVar5;
        *(int *)(*(int *)(param_1 + 0x28) + 0x74) = iVar5;
      }
      puVar1 = PTR_DAT_10006ac0;
      *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + 1;
      *(undefined4 *)(iVar5 + 0x30) = 5;
      *(undefined4 *)(iVar5 + 0x38) = 1;
      iVar3 = *(int *)puVar1;
      *(int *)(iVar5 + 0x4c) = param_3;
      *(int *)puVar1 = iVar3 + 1;
      wsr(0,uVar7);
      rsync();
      if (param_3 != -1) {
        FUN_1001a590(iVar5 + 0x4c,uVar7);
      }
      FUN_100176c8(iVar5);
      return *(undefined4 *)(iVar5 + 0x84);
    }
    uVar2 = 0xb;
    goto LAB_1001a378;
  }
  iVar5 = *(int *)(param_1 + 0x28);
  if (iVar5 != 0) {
    if (iVar5 == *(int *)(iVar5 + 0x70)) {
      *(undefined4 *)(param_1 + 0x28) = 0;
    }
    else {
      *(int *)(param_1 + 0x28) = *(int *)(iVar5 + 0x70);
      *(undefined4 *)(*(int *)(iVar5 + 0x70) + 0x74) = *(undefined4 *)(iVar5 + 0x74);
      *(undefined4 *)(*(int *)(iVar5 + 0x74) + 0x70) = *(undefined4 *)(iVar5 + 0x70);
    }
    puVar1 = PTR_DAT_10006ac0;
    *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + -1;
    iVar3 = *(int *)puVar1;
    *(undefined4 *)(iVar5 + 0x68) = 0;
    *(int *)puVar1 = iVar3 + 1;
    wsr(0,uVar7);
    rsync();
    uVar6 = *(uint *)(param_1 + 8);
    puVar4 = *(undefined4 **)(iVar5 + 0x7c);
    if (uVar6 != 2) {
      if (uVar6 < 3) {
        if (uVar6 == 1) goto LAB_1001a2d0;
LAB_1001a257:
        *puVar4 = *param_2;
        puVar4[1] = param_2[1];
        puVar4[2] = param_2[2];
        puVar4[3] = param_2[3];
        puVar4[4] = param_2[4];
        puVar4[5] = param_2[5];
        puVar4[6] = param_2[6];
        puVar4[7] = param_2[7];
        param_2 = param_2 + 8;
        puVar4 = puVar4 + 8;
LAB_1001a298:
        *puVar4 = *param_2;
        puVar4[1] = param_2[1];
        puVar4[2] = param_2[2];
        puVar4[3] = param_2[3];
        param_2 = param_2 + 4;
        puVar4 = puVar4 + 4;
      }
      else if (uVar6 != 4) {
        if (uVar6 != 8) goto LAB_1001a257;
        goto LAB_1001a298;
      }
      *puVar4 = *param_2;
      puVar4[1] = param_2[1];
      param_2 = param_2 + 2;
      puVar4 = puVar4 + 2;
    }
    *puVar4 = *param_2;
    param_2 = param_2 + 1;
    puVar4 = puVar4 + 1;
LAB_1001a2d0:
    *puVar4 = *param_2;
    if (*(int *)(iVar5 + 100) == 0) {
      *(undefined4 *)(iVar5 + 0x4c) = 0;
    }
    else {
      FUN_1001bac4(iVar5 + 0x4c);
    }
    *(undefined4 *)(iVar5 + 0x84) = 0;
    iVar5 = FUN_1001aac0(iVar5);
    if (iVar5 != 0) {
      FUN_10018750();
    }
    return 0;
  }
  *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + -1;
  puVar4 = *(undefined4 **)(param_1 + 0x24);
  uVar6 = *(uint *)(param_1 + 8);
  *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + 1;
  if (uVar6 == 2) {
LAB_1001a1d8:
    *puVar4 = *param_2;
    param_2 = param_2 + 1;
    puVar4 = puVar4 + 1;
  }
  else {
    if (2 < uVar6) {
      if (uVar6 != 4) {
        if (uVar6 != 8) goto LAB_1001a168;
        goto LAB_1001a1a8;
      }
LAB_1001a1c8:
      *puVar4 = *param_2;
      puVar4[1] = param_2[1];
      param_2 = param_2 + 2;
      puVar4 = puVar4 + 2;
      goto LAB_1001a1d8;
    }
    if (uVar6 != 1) {
LAB_1001a168:
      *puVar4 = *param_2;
      puVar4[1] = param_2[1];
      puVar4[2] = param_2[2];
      puVar4[3] = param_2[3];
      puVar4[4] = param_2[4];
      puVar4[5] = param_2[5];
      puVar4[6] = param_2[6];
      puVar4[7] = param_2[7];
      param_2 = param_2 + 8;
      puVar4 = puVar4 + 8;
LAB_1001a1a8:
      *puVar4 = *param_2;
      puVar4[1] = param_2[1];
      puVar4[2] = param_2[2];
      puVar4[3] = param_2[3];
      param_2 = param_2 + 4;
      puVar4 = puVar4 + 4;
      goto LAB_1001a1c8;
    }
  }
  *puVar4 = *param_2;
  uVar6 = *(int *)(param_1 + 8) * 4 + *(int *)(param_1 + 0x24);
  *(uint *)(param_1 + 0x24) = uVar6;
  if (*(uint *)(param_1 + 0x1c) <= uVar6) {
    *(undefined4 *)(param_1 + 0x24) = *(undefined4 *)(param_1 + 0x18);
  }
  uVar2 = 0;
LAB_1001a378:
  wsr(0,uVar7);
  rsync();
  return uVar2;
}


