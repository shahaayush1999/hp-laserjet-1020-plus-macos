/* Function: 10019408 FUN_10019408 */


undefined4 FUN_10019408(int param_1,uint param_2,uint param_3,undefined4 *param_4,int param_5)

{
  undefined *puVar1;
  int iVar2;
  undefined4 uVar3;
  int iVar4;
  undefined4 uVar5;
  
  puVar1 = PTR_LAB_10006b64;
  uVar5 = rsil(1);
  if ((param_3 & 2) == 0) {
    iVar2 = 7;
    if ((*(uint *)(param_1 + 8) & param_2) != 0) {
      iVar2 = 0;
    }
  }
  else {
    iVar2 = 7;
    if ((*(uint *)(param_1 + 8) & param_2) == param_2) {
      iVar2 = 0;
    }
  }
  if (iVar2 == 0) {
    *param_4 = *(undefined4 *)(param_1 + 8);
    uVar3 = 0;
    if ((param_3 & 1) != 0) {
      *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & (param_2 ^ 0xffffffff);
    }
  }
  else {
    if (param_5 != 0) {
      iVar2 = *(int *)PTR_DAT_10006a9c;
      *(uint *)(iVar2 + 0x78) = param_2;
      *(uint *)(iVar2 + 0x80) = param_3;
      *(undefined4 **)(iVar2 + 0x7c) = param_4;
      *(int *)(iVar2 + 0x6c) = param_1;
      *(undefined **)(iVar2 + 0x68) = puVar1;
      if (*(int *)(param_1 + 0x10) == 0) {
        *(int *)(param_1 + 0x10) = iVar2;
        *(int *)(iVar2 + 0x70) = iVar2;
        *(int *)(iVar2 + 0x74) = iVar2;
      }
      else {
        *(int *)(iVar2 + 0x70) = *(int *)(param_1 + 0x10);
        *(undefined4 *)(iVar2 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x10) + 0x74);
        *(int *)(*(int *)(*(int *)(param_1 + 0x10) + 0x74) + 0x70) = iVar2;
        *(int *)(*(int *)(param_1 + 0x10) + 0x74) = iVar2;
      }
      puVar1 = PTR_DAT_10006ac0;
      *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + 1;
      *(undefined4 *)(iVar2 + 0x30) = 7;
      *(undefined4 *)(iVar2 + 0x38) = 1;
      iVar4 = *(int *)puVar1;
      *(int *)(iVar2 + 0x4c) = param_5;
      *(int *)puVar1 = iVar4 + 1;
      wsr(0,uVar5);
      rsync();
      if (param_5 != -1) {
        FUN_1001a590(iVar2 + 0x4c,uVar5);
      }
      FUN_100176c8(iVar2);
      return *(undefined4 *)(iVar2 + 0x84);
    }
    uVar3 = 7;
  }
  wsr(0,uVar5);
  rsync();
  return uVar3;
}


