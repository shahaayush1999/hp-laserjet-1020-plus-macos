/* Function: 1001b9b8 FUN_1001b9b8 */


undefined4 FUN_1001b9b8(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  
  uVar3 = rsil(1);
  if (*(uint *)(param_1 + 0x2c) == 2) {
    iVar1 = *(int *)(*(int *)(param_1 + 0x28) + 0x70);
    if (*(uint *)(iVar1 + 0x2c) < *(uint *)(*(int *)(param_1 + 0x28) + 0x2c)) {
      *(int *)(param_1 + 0x28) = iVar1;
    }
  }
  else if (2 < *(uint *)(param_1 + 0x2c)) {
    iVar1 = *(int *)(param_1 + 0x28);
    iVar2 = *(int *)(iVar1 + 0x70);
    do {
      if (*(uint *)(iVar2 + 0x2c) < *(uint *)(iVar1 + 0x2c)) {
        iVar1 = iVar2;
      }
      iVar2 = *(int *)(iVar2 + 0x70);
    } while (iVar2 != *(int *)(param_1 + 0x28));
    if (iVar1 != iVar2) {
      *(undefined4 *)(*(int *)(iVar1 + 0x70) + 0x74) = *(undefined4 *)(iVar1 + 0x74);
      *(undefined4 *)(*(int *)(iVar1 + 0x74) + 0x70) = *(undefined4 *)(iVar1 + 0x70);
      *(undefined4 *)(iVar1 + 0x70) = *(undefined4 *)(param_1 + 0x28);
      *(undefined4 *)(iVar1 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x28) + 0x74);
      *(int *)(*(int *)(*(int *)(param_1 + 0x28) + 0x74) + 0x70) = iVar1;
      *(int *)(*(int *)(param_1 + 0x28) + 0x74) = iVar1;
      *(int *)(param_1 + 0x28) = iVar1;
    }
  }
  wsr(0,uVar3);
  rsync();
  return 0;
}


