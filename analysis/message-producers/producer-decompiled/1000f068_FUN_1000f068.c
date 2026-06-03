/* Function: 1000f068 FUN_1000f068 */


void FUN_1000f068(int *param_1,uint param_2)

{
  int iVar1;
  ushort uVar2;
  int iVar3;
  
  if (*param_1 == 0) {
    return;
  }
  iVar3 = *(int *)(*(int *)(*param_1 + 0xc) + 0x70);
  if (iVar3 == 0) {
    return;
  }
  iVar3 = *(int *)(iVar3 + 0xc);
  if (iVar3 == 0) {
    return;
  }
  iVar1 = *(int *)(iVar3 + 0x48);
  if ((iVar1 == 0) && (iVar1 = *(int *)(iVar3 + 0x4c), iVar1 == 0)) {
    return;
  }
  if ((param_2 & 8) != 0) {
    uVar2 = FUN_1000f0a8(iVar1 + 0x50,0);
    *(ushort *)(iVar1 + 0x4a) = *(ushort *)(iVar1 + 0x4a) | uVar2;
  }
  return;
}


