/* Function: 1000b128 FUN_1000b128 */


undefined4 FUN_1000b128(int param_1,undefined4 param_2,undefined4 param_3)

{
  undefined *puVar1;
  int iVar2;
  undefined4 uVar3;
  
  puVar1 = PTR_DAT_100060bc;
  if (*(int *)(*(int *)PTR_DAT_100060bc + 0x50) != 0) {
    FUN_10013408();
  }
  if (param_1 == 0) {
    *(undefined4 *)(*(int *)puVar1 + 0x50) = 0;
  }
  else {
    iVar2 = FUN_100169d4(param_1);
    uVar3 = FUN_1000dc00(iVar2 + 1);
    *(undefined4 *)(*(int *)puVar1 + 0x50) = uVar3;
    FUN_1001693c(uVar3,param_1);
  }
  iVar2 = *(int *)PTR_DAT_100060bc;
  *(undefined4 *)(iVar2 + 0x48) = param_2;
  *(undefined4 *)(iVar2 + 0x4c) = param_3;
  return 1;
}


