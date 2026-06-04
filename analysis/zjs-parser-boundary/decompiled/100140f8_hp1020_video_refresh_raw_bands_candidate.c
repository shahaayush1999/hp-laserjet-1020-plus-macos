/* Function: 100140f8 hp1020_video_refresh_raw_bands_candidate */


void hp1020_video_refresh_raw_bands_candidate(void)

{
  ushort uVar1;
  undefined2 uVar2;
  undefined *puVar3;
  uint *puVar4;
  int iVar5;
  int *piVar6;
  uint uVar7;
  int iVar8;
  uint uVar9;
  undefined4 uVar10;
  int iVar11;

  puVar3 = PTR_DAT_10006770;
  iVar11 = 0;
  for (piVar6 = *(int **)(PTR_DAT_10006770 + 0x9c); piVar6 != (int *)0x0; piVar6 = (int *)*piVar6) {
    iVar11 = iVar11 + 1;
  }
  FUN_10006f00(DAT_10005e74,PTR_s_refreshRawBands__ic_pBidBlock_0x_100067e0,
               *(undefined4 *)(PTR_DAT_10006770 + 0x9c),iVar11);
  memw();
  uVar7 = *DAT_100067c0;
  piVar6 = DAT_100067d0;
  while (((uVar7 & 0x100) != 0 && (*(int *)(puVar3 + 0x9c) != 0))) {
    iVar5 = *(int *)(*(int *)(puVar3 + 0x9c) + 0xc);
    iVar8 = *(int *)(iVar5 + 0x54);
    iVar11 = *(int *)(iVar5 + 0x50);
    DAT_100067d0 = piVar6;
    if (*(int *)PTR_DAT_100067c8 == 1) {
      uVar10 = *(undefined4 *)(puVar3 + 0xc4);
      memw();
      *DAT_100067cc = iVar8;
      uVar1 = *(ushort *)(iVar5 + 0x20);
      memw();
      *piVar6 = iVar8 + *(int *)(puVar3 + 0xbc);
      uVar7 = FUN_1001b668(uVar1 >> 1,uVar10);
      puVar4 = DAT_100067d8;
      memw();
      uVar9 = uVar7 | (uint)(*(short *)(iVar5 + 0x4c) != 0) << 0x18 | (uint)(iVar11 == 2) << 0x19;
      uVar7 = *DAT_100067c0;
      while ((uVar7 & 0x100) == 0) {
        memw();
        uVar7 = *DAT_100067c0;
      }
      iVar11 = *(int *)(puVar3 + 0xec);
      memw();
      *DAT_100067d4 = uVar9;
      memw();
      uVar7 = *puVar4;
      while ((uVar7 & 0x100) == 0) {
        memw();
        uVar7 = *puVar4;
      }
      memw();
      *DAT_100067dc = uVar9 | (uint)(iVar11 != 0) << 0x19;
    }
    else {
      uVar10 = *(undefined4 *)(puVar3 + 0xc4);
      uVar2 = *(undefined2 *)(iVar5 + 0x20);
      memw();
      *DAT_100067cc = iVar8;
      uVar7 = FUN_1001b668(uVar2,uVar10);
      memw();
      *DAT_100067d4 =
           uVar7 | (uint)(*(short *)(iVar5 + 0x4c) != 0) << 0x18 | (uint)(iVar11 == 2) << 0x19;
    }
    memw();
    uVar7 = *DAT_100067c0;
    *(undefined4 *)(puVar3 + 0x9c) = **(undefined4 **)(puVar3 + 0x9c);
    piVar6 = DAT_100067d0;
  }
  DAT_100067d0 = piVar6;
  return;
}
