/* Function: 1000fdbc FUN_1000fdbc */


undefined4 FUN_1000fdbc(uint *param_1)

{
  bool bVar1;
  undefined *puVar2;
  undefined4 uVar3;
  int iVar4;
  uint uVar5;
  bool bVar6;
  
  puVar2 = PTR_DAT_10006340;
  uVar3 = 1;
  bVar6 = false;
  if (((*param_1 & DAT_10005f74) == 0x100) ||
     ((undefined *)(*param_1 & DAT_10006358) == PTR_LAB_10006374)) {
    bVar6 = true;
  }
  uVar5 = *param_1;
  iVar4 = *(int *)PTR_DAT_10006340;
  bVar1 = (uVar5 & DAT_10005c88) != 0;
  if (iVar4 == 0) {
    if (bVar1) {
      *(uint *)(PTR_DAT_10006340 + 4) = uVar5;
      *(undefined4 *)puVar2 = 1;
      if ((*param_1 & DAT_1000637c) == 0) {
        *(undefined4 *)(puVar2 + 8) = 0;
      }
      else {
        *(undefined4 *)(puVar2 + 8) = 1;
      }
      if ((*param_1 & DAT_10005cf4) == 0) {
        *(undefined4 *)(PTR_DAT_10006340 + 0xc) = 0;
      }
      else {
        *(undefined4 *)(PTR_DAT_10006340 + 0xc) = 1;
      }
      uVar5 = DAT_10006388;
      if ((*param_1 & DAT_10006380) != 0) {
        uVar5 = DAT_10006384;
      }
      *param_1 = uVar5;
      iVar4 = FUN_100130bc(PTR_DAT_10006328);
      puVar2 = PTR_DAT_10006340;
      uVar3 = 1;
      if (iVar4 == 0) {
        *(undefined4 *)(PTR_DAT_10006340 + 0x2c) = 0;
      }
      else {
        iVar4 = *(int *)(iVar4 + 0xc);
        *(int *)(PTR_DAT_10006340 + 0x2c) = iVar4;
        *(uint *)(puVar2 + 0x1c) = (uint)*(ushort *)(iVar4 + 0x7c);
        *(uint *)(puVar2 + 0x24) = (uint)*(ushort *)(iVar4 + 0x80);
        *(uint *)(puVar2 + 0x20) = (uint)*(ushort *)(iVar4 + 0x7e);
        *(uint *)(puVar2 + 0x14) = (uint)*(ushort *)(iVar4 + 10);
        *(uint *)(puVar2 + 0x18) = (uint)*(ushort *)(iVar4 + 0x10);
        *(uint *)(puVar2 + 0x10) = (uint)*(ushort *)(iVar4 + 0xe);
      }
    }
  }
  else if ((iVar4 == 1) ||
          ((iVar4 == 3 &&
           ((((*(int *)(PTR_DAT_10006340 + 8) == 1 && (bVar6)) || (bVar1)) ||
            ((uVar5 & DAT_10006378) < (*(uint *)(PTR_DAT_10006338 + 0x10) & DAT_10006378))))))) {
    uVar3 = 0;
  }
  return uVar3;
}


