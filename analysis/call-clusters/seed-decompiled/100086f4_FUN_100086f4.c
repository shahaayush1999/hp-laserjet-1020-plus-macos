/* Function: 100086f4 FUN_100086f4 */


void FUN_100086f4(int param_1)

{
  undefined *puVar1;
  int *piVar2;
  undefined *puVar3;
  undefined1 uVar5;
  undefined1 *puVar4;
  int iVar6;
  uint uVar7;
  
  uVar7 = *(uint *)PTR_DAT_10005e54;
  if ((uVar7 == 0) || ((uVar7 & 0xf) != 0)) {
    iVar6 = *(int *)PTR_DAT_10005e2c;
    param_1 = *(int *)PTR_DAT_10005e44 + param_1;
    *(char *)(iVar6 + 8) = (char)((uint)param_1 >> 0x18);
    *(char *)(iVar6 + 9) = (char)((uint)param_1 >> 0x10);
    *(char *)(iVar6 + 10) = (char)((uint)param_1 >> 8);
    *(char *)(iVar6 + 0xb) = (char)param_1;
    uVar5 = 0;
  }
  else {
    iVar6 = *(int *)PTR_DAT_10005e2c;
    *(char *)(iVar6 + 8) = (char)(uVar7 >> 0x18);
    *(char *)(iVar6 + 9) = (char)(uVar7 >> 0x10);
    *(char *)(iVar6 + 10) = (char)(uVar7 >> 8);
    *(char *)(iVar6 + 0xb) = (char)uVar7;
    uVar5 = 1;
  }
  *PTR_DAT_10005e28 = uVar5;
  piVar2 = DAT_10005e60;
  puVar1 = PTR_DAT_10005e2c;
  iVar6 = *(int *)PTR_DAT_10005e2c;
  *PTR_DAT_10005e58 = 0;
  memw();
  *piVar2 = iVar6;
  *(undefined1 *)(iVar6 + 0xc) = 0;
  *(undefined1 *)(iVar6 + 0xd) = 0;
  *(undefined1 *)(iVar6 + 0xe) = 0;
  *(undefined1 *)(iVar6 + 0xf) = 0;
  puVar4 = *(undefined1 **)puVar1;
  memw();
  memw();
  *puVar4 = 8;
  memw();
  memw();
  puVar4[1] = 0;
  memw();
  memw();
  puVar4[2] = 0;
  puVar1 = PTR_DAT_10005e20;
  memw();
  memw();
  puVar4[3] = 0;
  puVar3 = PTR_DAT_10005e64;
  *puVar1 = 1;
  *puVar3 = 0;
  return;
}


