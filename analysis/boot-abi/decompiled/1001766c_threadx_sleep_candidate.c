/* Function: 1001766c threadx_sleep_candidate */


undefined4 threadx_sleep_candidate(int param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  
  puVar2 = PTR_DAT_10006ac0;
  puVar1 = PTR_DAT_10006a9c;
  if (((*(undefined **)PTR_DAT_10006a9c != (undefined *)0x0) &&
      (*(undefined **)PTR_DAT_10006a9c != PTR_DAT_10006ae8)) && (*(int *)PTR_DAT_10005d80 == 0)) {
    if (param_1 == 0) {
      return 0;
    }
    uVar5 = rsil(1);
    iVar4 = *(int *)PTR_DAT_10006a9c;
    *(undefined4 *)(iVar4 + 0x30) = 4;
    *(undefined4 *)(iVar4 + 0x38) = 1;
    iVar3 = *(int *)puVar2;
    *(undefined4 *)(iVar4 + 0x84) = 0;
    *(int *)puVar2 = iVar3 + 1;
    wsr(0,uVar5);
    rsync();
    iVar3 = *(int *)puVar1;
    *(int *)(iVar3 + 0x4c) = param_1;
    FUN_1001a590(iVar3 + 0x4c,uVar5);
    FUN_100176c8(*(undefined4 *)puVar1);
    return *(undefined4 *)(*(int *)puVar1 + 0x84);
  }
  return 0x13;
}


