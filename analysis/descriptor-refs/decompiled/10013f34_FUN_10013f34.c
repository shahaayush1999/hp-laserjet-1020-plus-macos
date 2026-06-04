/* Function: 10013f34 FUN_10013f34 */


void FUN_10013f34(void)

{
  undefined *puVar1;
  undefined *puVar2;
  uint *puVar3;
  undefined *puVar4;
  int *piVar5;
  undefined *puVar6;
  int iVar7;
  uint uVar8;
  uint uVar9;
  undefined4 *puVar10;
  undefined4 uVar11;
  undefined4 uVar12;
  
  puVar4 = PTR_DAT_100067c4;
  puVar2 = PTR_DAT_10006770;
  puVar6 = PTR_DAT_100067bc + *(int *)(PTR_DAT_10006770 + 0xdc) * 0xc;
  memw();
  uVar8 = *DAT_100067c0;
  puVar1 = PTR_DAT_10006770;
  while (((uVar8 & 0x100) != 0 &&
         (((*(int *)(puVar2 + 0xdc) + 1U & 3) != *(uint *)(puVar2 + 0xe0) ||
          (*(int *)(puVar6 + 4) != 0))))) {
    iVar7 = *(int *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4);
    PTR_DAT_10006770 = puVar1;
    if (*(int *)(puVar2 + 0xc0) != 0) {
      if (*(int *)puVar4 != 0) {
        if (*(int *)(puVar6 + 4) != 0) {
          uVar8 = 0;
          puVar10 = (undefined4 *)(iVar7 + *(int *)(puVar6 + 8) * *(uint *)(puVar2 + 0xb8));
          if ((*(uint *)(puVar2 + 0xb8) >> 2) * *(int *)(puVar2 + 0xf4) != 0) {
            do {
              *puVar10 = 0;
              puVar10 = puVar10 + 1;
              uVar8 = uVar8 + 1;
            } while (uVar8 < (*(uint *)(puVar1 + 0xb8) >> 2) * *(int *)(puVar1 + 0xf4));
          }
        }
        if (*(uint *)(puVar2 + 0xd4) <= (uint)(*(int *)(puVar6 + 8) << 2)) {
          if (*(uint *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10) <= DAT_1000628c) {
            *(uint *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10) =
                 *(uint *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10) + DAT_10005e34;
          }
        }
        (**(code **)puVar4)(iVar7 - *(int *)(puVar2 + 0xf4) * *(int *)(puVar2 + 0xb8),
                            *(undefined4 *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10),
                            *(uint *)(puVar6 + 8) & 0xfffffffc);
      }
      if ((*(int *)(puVar2 + 0xc0) != 0) && (*(int *)puVar4 != 0)) {
        iVar7 = *(int *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10);
      }
    }
    piVar5 = DAT_100067d0;
    if (*(int *)PTR_DAT_100067c8 == 1) {
      uVar11 = *(undefined4 *)(puVar2 + 0xc4);
      memw();
      *DAT_100067cc = iVar7;
      uVar8 = *(uint *)(puVar6 + 8);
      memw();
      *piVar5 = iVar7 + *(int *)(puVar2 + 0xbc);
      uVar9 = FUN_1001b668(uVar8 >> 1,uVar11);
      puVar3 = DAT_100067d8;
      memw();
      uVar9 = uVar9 | (uint)(*(int *)(puVar6 + 4) != 0) << 0x18;
      uVar8 = *DAT_100067c0;
      while ((uVar8 & 0x100) == 0) {
        memw();
        uVar8 = *DAT_100067c0;
      }
      memw();
      *DAT_100067d4 = uVar9;
      memw();
      uVar8 = *puVar3;
      while ((uVar8 & 0x100) == 0) {
        memw();
        uVar8 = *puVar3;
      }
      memw();
      *DAT_100067dc = uVar9 | (uint)(*(int *)(puVar2 + 0xec) != 0) << 0x19;
    }
    else {
      uVar12 = *(undefined4 *)(puVar2 + 0xc4);
      uVar11 = *(undefined4 *)(puVar6 + 8);
      memw();
      *DAT_100067cc = iVar7;
      uVar8 = FUN_1001b668(uVar11,uVar12);
      memw();
      *DAT_100067d4 = uVar8 | (uint)(*(int *)(puVar6 + 4) != 0) << 0x18;
    }
    puVar1 = PTR_DAT_100067bc;
    *(int *)(puVar2 + 0xd4) = *(int *)(puVar2 + 0xd4) - *(int *)(puVar6 + 8);
    puVar3 = DAT_100067c0;
    uVar9 = *(int *)(puVar2 + 0xdc) + 1U & 3;
    *(uint *)(puVar2 + 0xdc) = uVar9;
    memw();
    uVar8 = *puVar3;
    puVar6 = puVar1 + uVar9 * 0xc;
    puVar1 = PTR_DAT_10006770;
  }
  PTR_DAT_10006770 = puVar1;
  return;
}


