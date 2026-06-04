/* Function: 10018eac FUN_10018eac */


undefined4 FUN_10018eac(int param_1,int *param_2,int param_3,int param_4)

{
  undefined *puVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  int iVar5;
  undefined4 uVar6;
  uint uVar7;

  uVar7 = 0;
  iVar5 = *(int *)PTR_DAT_10006a9c;
  uVar4 = param_3 + 3U & 0xfffffffc;
  uVar6 = rsil(1);
  do {
    *(int *)(param_1 + 0x20) = iVar5;
    wsr((char)uVar7,uVar6);
    rsync();
    uVar7 = uVar7 & 0xffffcfff;
    iVar2 = FUN_10019234(param_1,uVar4);
    uVar6 = rsil(1);
    if (iVar2 != 0) {
      *param_2 = iVar2;
      uVar3 = 0;
      goto LAB_10018f5c;
    }
  } while (*(int *)(param_1 + 0x20) != iVar5);
  if (param_4 != 0) {
    *(int *)(iVar5 + 0x6c) = param_1;
    *(int **)(iVar5 + 0x7c) = param_2;
    puVar1 = PTR_LAB_10006b48;
    *(uint *)(iVar5 + 0x78) = uVar4;
    *(undefined **)(iVar5 + 0x68) = puVar1;
    if (*(int *)(param_1 + 0x24) == 0) {
      *(int *)(param_1 + 0x24) = iVar5;
      *(int *)(iVar5 + 0x70) = iVar5;
      *(int *)(iVar5 + 0x74) = iVar5;
    }
    else {
      *(int *)(iVar5 + 0x70) = *(int *)(param_1 + 0x24);
      *(undefined4 *)(iVar5 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x24) + 0x74);
      *(int *)(*(int *)(*(int *)(param_1 + 0x24) + 0x74) + 0x70) = iVar5;
      *(int *)(*(int *)(param_1 + 0x24) + 0x74) = iVar5;
    }
    puVar1 = PTR_DAT_10006ac0;
    *(int *)(param_1 + 0x28) = *(int *)(param_1 + 0x28) + 1;
    *(undefined4 *)(iVar5 + 0x30) = 9;
    *(undefined4 *)(iVar5 + 0x38) = 1;
    iVar2 = *(int *)puVar1;
    *(int *)(iVar5 + 0x4c) = param_4;
    *(int *)puVar1 = iVar2 + 1;
    wsr((char)uVar7,uVar6);
    rsync();
    if (param_4 != -1) {
      FUN_1001a590(iVar5 + 0x4c,uVar6);
    }
    FUN_100176c8(iVar5);
    return *(undefined4 *)(iVar5 + 0x84);
  }
  uVar3 = 0x10;
LAB_10018f5c:
  wsr((char)uVar7,uVar6);
  rsync();
  return uVar3;
}
