/* Function: 1000ded8 FUN_1000ded8 */


undefined4 FUN_1000ded8(undefined1 *param_1)

{
  bool bVar1;
  bool bVar2;
  bool bVar3;
  bool bVar4;
  bool bVar5;
  undefined *puVar6;
  int iVar7;
  int iVar8;
  undefined1 *puVar9;
  undefined4 uStack_30;

  puVar6 = PTR_DAT_10006288;
  bVar5 = false;
  bVar2 = false;
  bVar1 = *(int *)PTR_DAT_10006270 - 0x30U < 10;
  bVar4 = false;
  uStack_30 = 6;
  *param_1 = PTR_DAT_10006270[3];
  iVar7 = 1;
  iVar8 = *(int *)(puVar6 + 0xac);
  while (iVar8 == 0) {
    FUN_1000d6b0();
    iVar8 = *(int *)PTR_DAT_10006270;
    bVar3 = false;
    if (iVar8 - 0x30U < 10) {
      bVar3 = true;
      bVar1 = true;
    }
    else if (((iVar8 == 0x20) || (iVar8 == 9)) || (iVar8 == 10)) {
      if (bVar1) {
        bVar5 = true;
      }
      else {
        *(undefined4 *)(puVar6 + 0xac) = 0xd;
      }
    }
    else if (iVar8 == 0x2e) {
      if (bVar2) {
        *(undefined4 *)(puVar6 + 0xac) = 0x19;
      }
      else if (bVar1) {
        uStack_30 = 7;
        bVar3 = true;
        bVar2 = true;
      }
      else {
        *(undefined4 *)(puVar6 + 0xac) = 0xc;
      }
    }
    else if (iVar8 < 0x21) {
      *(undefined4 *)(puVar6 + 0xac) = 6;
      if (iVar8 != -1) {
        FUN_1000dd60();
      }
    }
    else {
      *(undefined4 *)(puVar6 + 0xac) = 9;
    }
    if (bVar3) {
      if (iVar7 < 0x50) {
        puVar9 = param_1 + iVar7;
        iVar7 = iVar7 + 1;
        *puVar9 = PTR_DAT_10006270[3];
      }
      else if (!bVar4) {
        FUN_1000dda8(5);
        bVar4 = true;
      }
    }
    if (bVar5) break;
    iVar8 = *(int *)(puVar6 + 0xac);
  }
  param_1[iVar7] = 0;
  return uStack_30;
}
