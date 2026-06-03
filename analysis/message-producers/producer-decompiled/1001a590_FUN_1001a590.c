/* Function: 1001a590 FUN_1001a590 */


undefined4 FUN_1001a590(uint *param_1)

{
  uint uVar1;
  uint *puVar2;
  int iVar3;
  undefined4 uVar4;
  
  uVar4 = rsil(1);
  uVar1 = *param_1;
  if ((uVar1 != 0) && (param_1[6] == 0)) {
    iVar3 = 0x1f;
    if (uVar1 < 0x21) {
      iVar3 = uVar1 - 1;
    }
    puVar2 = (uint *)(iVar3 * 4 + *(int *)PTR_DAT_10006adc);
    if (*(uint **)PTR_DAT_10006ae0 <= puVar2) {
      puVar2 = (uint *)(((int)puVar2 - (int)*(uint **)PTR_DAT_10006ae0 >> 2) * 4 +
                       *(int *)PTR_DAT_10006ad8);
    }
    if (*puVar2 == 0) {
      param_1[4] = (uint)param_1;
      param_1[5] = (uint)param_1;
      param_1[6] = (uint)puVar2;
      *puVar2 = (uint)param_1;
    }
    else {
      param_1[4] = *puVar2;
      uVar1 = *(uint *)(*puVar2 + 0x14);
      param_1[5] = uVar1;
      *(uint **)(uVar1 + 0x10) = param_1;
      *(uint **)(*puVar2 + 0x14) = param_1;
      param_1[6] = (uint)puVar2;
    }
  }
  wsr(0,uVar4);
  rsync();
  return 0;
}


