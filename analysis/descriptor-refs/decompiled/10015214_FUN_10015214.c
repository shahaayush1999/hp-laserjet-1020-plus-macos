/* Function: 10015214 FUN_10015214 */


undefined4 FUN_10015214(int param_1)

{
  undefined *puVar1;
  uint *puVar2;
  uint *puVar3;
  int *piVar4;
  undefined4 *puVar5;
  undefined4 uVar6;
  uint uVar7;
  int iVar8;
  undefined4 uVar9;
  uint uVar10;
  undefined4 uVar11;
  
  puVar1 = PTR_DAT_10006770;
  uVar7 = *(int *)(PTR_DAT_10006770 + 0x98) + 1U & 3;
  uVar6 = FUN_1001b770(1);
  iVar8 = *(int *)(param_1 + 0x50);
  *(int *)(puVar1 + 0x9c) = iVar8;
  iVar8 = *(int *)(iVar8 + 0xc);
  *(undefined4 *)(puVar1 + 0xa0) = 0;
  puVar2 = DAT_10006798;
  if (1 < *(int *)(puVar1 + 0x6c) - 1U) {
    FUN_1001b770();
    return DAT_1000683c;
  }
  if (*(uint *)(puVar1 + 0x94) == uVar7) {
    FUN_1001b770(uVar6);
    return DAT_1000683c;
  }
  uVar9 = *(undefined4 *)(iVar8 + 0x54);
  iVar8 = *(int *)(iVar8 + 0x48);
  if (*(int *)(puVar1 + 0x6c) != 2) {
    memw();
    memw();
    *DAT_10006798 = *DAT_10006798 | 2;
    puVar3 = DAT_1000679c;
    memw();
    memw();
    *puVar2 = *puVar2 & 0xfffffffd;
    puVar2 = DAT_10006798;
    memw();
    uVar10 = *puVar3;
    while ((uVar10 & 2) == 0) {
      memw();
      uVar10 = *puVar3;
    }
    memw();
    memw();
    *DAT_10006798 = *DAT_10006798 | 1;
    memw();
    memw();
    *puVar2 = *puVar2 | DAT_10005e34;
    FUN_10017184(0x14);
    puVar2 = DAT_10006794;
    memw();
    memw();
    *DAT_10006794 = *DAT_10006794 | 2;
    puVar3 = DAT_100067a0;
    memw();
    memw();
    *puVar2 = *puVar2 & 0xfffffffd;
    puVar2 = DAT_10006794;
    memw();
    uVar10 = *puVar3;
    while ((uVar10 & 2) == 0) {
      memw();
      uVar10 = *puVar3;
    }
    memw();
    memw();
    *DAT_10006794 = *DAT_10006794 | 1;
    memw();
    memw();
    *puVar2 = *puVar2 | DAT_10005e34;
    FUN_10017184(0x15);
    puVar1 = PTR_DAT_100068ec;
    puVar2 = DAT_10006790;
    *(undefined4 *)PTR_DAT_100068ec = 0;
    puVar5 = DAT_100068f0;
    memw();
    uVar11 = *(undefined4 *)(param_1 + 0x84);
    memw();
    *puVar2 = *puVar2 & 0xfffffffe;
    memw();
    *puVar5 = uVar11;
    puVar5 = DAT_100068f8;
    uVar11 = *(undefined4 *)(param_1 + 0x8c);
    memw();
    *DAT_100068f4 = *(undefined4 *)(param_1 + 0x88);
    memw();
    *puVar5 = uVar11;
    if ((*(byte *)(param_1 + 0x90) & 0x40) == 0) {
      *(undefined4 *)puVar1 = DAT_10005f5c;
    }
    else {
      *(undefined4 *)puVar1 = 0;
    }
    if ((*(byte *)(param_1 + 0x90) & 8) == 0) {
      uVar10 = *(uint *)PTR_DAT_100068ec & DAT_100068fc;
    }
    else {
      uVar10 = *(uint *)PTR_DAT_100068ec | DAT_10005dc8;
    }
    *(uint *)PTR_DAT_100068ec = uVar10;
    puVar2 = DAT_10006900;
    uVar10 = *(uint *)PTR_DAT_100068ec;
    *(uint *)PTR_DAT_100068ec = uVar10 | 0x400;
    memw();
    *puVar2 = uVar10 | 0x400;
  }
  puVar1 = PTR_DAT_10006770;
  if (*(int *)(PTR_DAT_10006770 + 0x98) == *(int *)(PTR_DAT_10006770 + 0x94)) {
    FUN_10017414(uVar9,iVar8);
    piVar4 = DAT_100067f8;
    memw();
    *DAT_100067f4 = uVar9;
    uVar9 = *(undefined4 *)(puVar1 + 0x9c);
    memw();
    *piVar4 = iVar8;
    *(undefined4 *)(puVar1 + 0xa4) = uVar9;
  }
  *(uint *)(puVar1 + 0x98) = uVar7;
  if (*(int *)(puVar1 + 0x6c) != 2) {
    FUN_10014244();
    do {
      memw();
    } while ((uint)(iVar8 - *DAT_100067f8) < 8);
    memw();
    memw();
    *DAT_10006790 = *DAT_10006790 | 1;
    FUN_10017184(0x13);
    *(undefined4 *)(PTR_DAT_10006770 + 0x6c) = 2;
  }
  FUN_1001b770(uVar6);
  return 0;
}


