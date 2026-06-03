/* Function: 1001a478 FUN_1001a478 */


undefined4 FUN_1001a478(int param_1,int param_2)

{
  undefined *puVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  
  puVar1 = PTR_LAB_10006b88;
  uVar5 = rsil(1);
  if (*(int *)(param_1 + 8) == 0) {
    if (param_2 != 0) {
      iVar3 = *(int *)PTR_DAT_10006a9c;
      *(int *)(iVar3 + 0x6c) = param_1;
      *(undefined **)(iVar3 + 0x68) = puVar1;
      if (*(int *)(param_1 + 0xc) == 0) {
        *(int *)(param_1 + 0xc) = iVar3;
        *(int *)(iVar3 + 0x70) = iVar3;
        *(int *)(iVar3 + 0x74) = iVar3;
      }
      else {
        *(int *)(iVar3 + 0x70) = *(int *)(param_1 + 0xc);
        *(undefined4 *)(iVar3 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0xc) + 0x74);
        *(int *)(*(int *)(*(int *)(param_1 + 0xc) + 0x74) + 0x70) = iVar3;
        *(int *)(*(int *)(param_1 + 0xc) + 0x74) = iVar3;
      }
      puVar1 = PTR_DAT_10006ac0;
      *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + 1;
      *(undefined4 *)(iVar3 + 0x30) = 6;
      *(undefined4 *)(iVar3 + 0x38) = 1;
      iVar4 = *(int *)puVar1;
      *(int *)(iVar3 + 0x4c) = param_2;
      *(int *)puVar1 = iVar4 + 1;
      wsr(0,uVar5);
      rsync();
      if (param_2 != -1) {
        FUN_1001a590(iVar3 + 0x4c);
      }
      FUN_100176c8(iVar3);
      return *(undefined4 *)(iVar3 + 0x84);
    }
    uVar2 = 0xd;
  }
  else {
    *(int *)(param_1 + 8) = *(int *)(param_1 + 8) + -1;
    uVar2 = 0;
  }
  wsr(0,uVar5);
  rsync();
  return uVar2;
}


