/* Function: 1000899c FUN_1000899c */


undefined4 FUN_1000899c(int *param_1)

{
  uint *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  uint *puVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  byte *pbVar9;
  int iVar10;
  undefined1 *puVar11;
  
  puVar3 = PTR_DAT_10005e7c;
  puVar2 = PTR_DAT_10005e50;
  iVar6 = param_1[2];
  iVar5 = *(int *)PTR_DAT_10005e50;
  if (iVar5 < iVar6) {
    iVar8 = *(int *)PTR_DAT_10005e7c;
    iVar10 = *param_1 + DAT_10005e34;
    *(char *)(iVar8 + 8) = (char)((uint)iVar10 >> 0x18);
    *(char *)(iVar8 + 9) = (char)((uint)iVar10 >> 0x10);
    *(char *)(iVar8 + 10) = (char)((uint)iVar10 >> 8);
    *(char *)(iVar8 + 0xb) = (char)iVar10;
    iVar10 = *(int *)puVar2;
    puVar11 = *(undefined1 **)puVar3;
    *param_1 = *param_1 + iVar10;
    memw();
    memw();
    *puVar11 = (char)((uint)iVar10 >> 0x18);
    memw();
    memw();
    puVar11[1] = (char)((uint)iVar10 >> 0x10);
    memw();
    memw();
    puVar11[2] = (char)((uint)iVar10 >> 8);
    memw();
    memw();
    puVar11[3] = (char)iVar10;
    iVar10 = *(int *)puVar3;
    iVar8 = iVar10 + 0x10;
    *(char *)(iVar10 + 0xc) = (char)((uint)iVar8 >> 0x18);
    *(char *)(iVar10 + 0xd) = (char)((uint)iVar8 >> 0x10);
    *(char *)(iVar10 + 0xe) = (char)((uint)iVar8 >> 8);
    *(char *)(iVar10 + 0xf) = (char)iVar8;
    param_1[2] = param_1[2] - *(int *)puVar2;
  }
  puVar2 = PTR_DAT_10005e7c;
  uVar7 = (uint)(iVar5 < iVar6);
  if (uVar7 == 1) {
    pbVar9 = *(byte **)PTR_DAT_10005e7c;
    memw();
    uVar7 = (uint)pbVar9[3] | (uint)pbVar9[2] << 8 | (uint)pbVar9[1] << 0x10 | (uint)*pbVar9 << 0x18
            | DAT_10005e80;
    memw();
    *pbVar9 = (byte)(uVar7 >> 0x18);
    memw();
    memw();
    pbVar9[1] = (byte)(uVar7 >> 0x10);
    memw();
    memw();
    pbVar9[2] = (byte)(uVar7 >> 8);
    memw();
    memw();
    pbVar9[3] = (byte)uVar7;
  }
  else {
    iVar10 = uVar7 * 0x10;
    iVar6 = *param_1 + DAT_10005e34;
    iVar5 = iVar10 + *(int *)PTR_DAT_10005e7c;
    *(char *)(iVar5 + 8) = (char)((uint)iVar6 >> 0x18);
    *(char *)(iVar5 + 9) = (char)((uint)iVar6 >> 0x10);
    *(char *)(iVar5 + 10) = (char)((uint)iVar6 >> 8);
    *(char *)(iVar5 + 0xb) = (char)iVar6;
    iVar5 = iVar10 + *(int *)puVar2;
    *(undefined1 *)(iVar5 + 0xc) = 0;
    *(undefined1 *)(iVar5 + 0xd) = 0;
    *(undefined1 *)(iVar5 + 0xe) = 0;
    *(undefined1 *)(iVar5 + 0xf) = 0;
    puVar11 = (undefined1 *)(iVar10 + *(int *)puVar2);
    memw();
    uVar7 = param_1[2] | DAT_10005e80;
    memw();
    *puVar11 = (char)(uVar7 >> 0x18);
    memw();
    memw();
    puVar11[1] = (char)(uVar7 >> 0x10);
    memw();
    memw();
    puVar11[2] = (char)(uVar7 >> 8);
    memw();
    memw();
    puVar11[3] = (char)uVar7;
    param_1[2] = 0;
  }
  puVar4 = DAT_10005e88;
  puVar1 = DAT_10005e00;
  memw();
  *DAT_10005e84 = *(undefined4 *)PTR_DAT_10005e7c;
  memw();
  memw();
  *puVar1 = *puVar1 & 0xfffffffd;
  memw();
  memw();
  *puVar4 = *puVar4 | 8;
  return 0;
}


