/* Function: 10014910 FUN_10014910 */


undefined4 FUN_10014910(int param_1)

{
  uint *puVar1;
  uint *puVar2;
  uint *puVar3;
  undefined *puVar4;
  int iVar5;
  undefined4 uVar6;
  uint uVar7;
  int iVar8;
  undefined *puVar9;
  int iVar10;
  undefined4 *puVar11;
  undefined4 *puVar12;
  ushort uVar13;
  int iVar14;
  undefined *puVar15;
  undefined4 uVar16;
  short sVar17;
  short sVar18;
  uint uVar19;
  int iVar20;
  int iVar21;
  undefined1 uVar22;
  uint local_30;
  uint uStack_2c;
  
  local_30 = 0xc;
  uStack_2c = 0;
  uVar6 = rsil(1);
  uVar22 = 0;
  iVar5 = FUN_10011178(0x20);
  puVar15 = PTR_DAT_10006770;
  *(undefined4 *)(PTR_DAT_10006770 + 0xc0) = 0;
  if ((iVar5 == 0) && (*(short *)(param_1 + 0x36) == 0)) {
    *(undefined4 *)(puVar15 + 0xc0) = 1;
  }
  puVar15 = PTR_DAT_10006770;
  if (*(int *)(PTR_DAT_10006770 + 0x6c) != 0) {
    wsr(uVar22,uVar6);
    rsync();
    uVar6 = DAT_1000683c;
    if (*(int *)(PTR_DAT_10006770 + 0x6c) == 3) {
      uVar6 = *(undefined4 *)(PTR_DAT_10006770 + 0x68);
    }
    return uVar6;
  }
  wsr(uVar22,uVar6);
  rsync();
  FUN_100181a4(PTR_DAT_10006810,0xffffffff);
  *(undefined4 *)(puVar15 + 0x70) = 1;
  FUN_100171b0(10);
  FUN_100171b0(0xb);
  FUN_100171b0(0x13);
  FUN_100171b0(0x14);
  FUN_100171b0(0x15);
  puVar4 = PTR_DAT_10006840;
  memw();
  *(undefined4 *)PTR_DAT_10006840 = 0;
  memw();
  uVar7 = *(uint *)puVar4;
  puVar9 = PTR_DAT_10006770;
  puVar1 = (uint *)PTR_DAT_10006840;
  while (PTR_DAT_10006770 = puVar9, PTR_DAT_10006840 = (undefined *)puVar1, uVar7 < 5) {
    memw();
    iVar8 = *(int *)puVar4;
    memw();
    memw();
    *(int *)puVar4 = *(int *)puVar4 + 1;
    memw();
    uVar7 = *(uint *)puVar4;
    *(undefined4 *)(puVar15 + iVar8 * 4 + 0xa4) = 0;
    puVar9 = PTR_DAT_10006770;
    puVar1 = (uint *)PTR_DAT_10006840;
  }
  *(undefined4 *)(puVar9 + 0xf8) = 0;
  *(undefined4 *)(puVar9 + 0x98) = 0;
  *(undefined4 *)(puVar9 + 0x94) = 0;
  *(undefined4 *)(puVar9 + 0xd8) = 0;
  *(undefined4 *)(puVar9 + 0xdc) = 0;
  memw();
  *puVar1 = 0;
  memw();
  uVar7 = *puVar1;
  *(undefined4 *)(puVar9 + 0xe0) = 0;
  uVar6 = DAT_10005dc8;
  puVar15 = PTR_DAT_10006770;
  while (DAT_10005dc8 = uVar6, PTR_DAT_10006770 = puVar15, uVar7 < 4) {
    memw();
    memw();
    uVar19 = *puVar1;
    memw();
    uVar7 = *puVar1;
    *(undefined4 *)(puVar9 + *puVar1 * 0xc + 0x20) = 0;
    memw();
    *puVar1 = uVar7 + 1;
    memw();
    uVar7 = *puVar1;
    *(undefined4 *)(puVar9 + uVar19 * 0xc + 0x24) = 0;
    uVar6 = DAT_10005dc8;
    puVar15 = PTR_DAT_10006770;
  }
  *(undefined4 *)(puVar15 + 0xf0) = 0;
  uVar19 = (*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3;
  *(uint *)(puVar15 + 0xb8) = uVar19;
  uVar7 = FUN_1001b668(uVar6,uVar19);
  *(uint *)(puVar15 + 0xcc) = uVar7 & 0xfffffffc;
  *(uint *)(puVar15 + 0xbc) = uVar19;
  *(undefined4 *)(puVar15 + 0xc4) = 1;
  uVar7 = (uint)*(ushort *)(param_1 + 0x22);
  *(uint *)(puVar15 + 200) = uVar7;
  *(undefined4 *)(puVar15 + 0xf4) = 0;
  puVar9 = PTR_LAB_1000684c;
  puVar12 = (undefined4 *)PTR_DAT_100067c4;
  if (*(int *)(puVar15 + 0xc0) != 0) {
    if (uVar7 == 1) {
      sVar18 = *(short *)(param_1 + 0x14);
      if (sVar18 == 300) {
        *(undefined4 *)PTR_DAT_100067c4 = 0;
      }
      else {
        if (sVar18 == 600) {
          *(undefined4 *)(puVar15 + 0xf4) = 2;
          *(uint *)(puVar15 + 0xbc) = uVar19 << 1;
          puVar9 = PTR_DAT_10006844;
          puVar12 = (undefined4 *)PTR_DAT_100067c4;
          *(undefined4 *)(puVar15 + 200) = 2;
        }
        else {
          if (sVar18 != 0x4b0) goto LAB_10014ae0;
          *(undefined4 *)(puVar15 + 0xf4) = 4;
          *(uint *)(puVar15 + 0xbc) = uVar19 << 1;
          *(undefined4 *)(puVar15 + 0xc4) = 2;
          puVar9 = PTR_DAT_10006848;
          puVar12 = (undefined4 *)PTR_DAT_100067c4;
          *(undefined4 *)(puVar15 + 200) = 4;
        }
LAB_10014add:
        *puVar12 = puVar9;
      }
    }
    else if ((uVar7 == 2) && (*(short *)(param_1 + 0x14) == 600)) {
      *(undefined4 *)(puVar15 + 0xf4) = 2;
      goto LAB_10014add;
    }
  }
LAB_10014ae0:
  puVar15 = PTR_DAT_10006770;
  iVar8 = *(int *)(PTR_DAT_10006770 + 0xb8);
  uVar6 = FUN_1001b668(DAT_10005ddc,iVar8);
  puVar4 = PTR_DAT_10006840;
  puVar9 = PTR_DAT_10006830;
  memw();
  *(undefined4 *)PTR_DAT_10006840 = uVar6;
  iVar20 = *(int *)puVar9;
  *(int *)(puVar15 + 0x50) = iVar20;
  memw();
  iVar14 = *(int *)puVar4;
  iVar10 = iVar20 + *(int *)(puVar15 + 0xf4) * iVar8;
  iVar8 = iVar8 * 4;
  *(int *)puVar15 = iVar10;
  iVar10 = iVar10 + iVar14 * iVar8;
  memw();
  iVar14 = *(int *)puVar4;
  *(int *)(puVar15 + 4) = iVar10;
  iVar10 = iVar10 + iVar14 * iVar8;
  memw();
  iVar14 = *(int *)puVar4;
  *(int *)(puVar15 + 8) = iVar10;
  memw();
  iVar21 = *(int *)puVar4;
  iVar10 = iVar10 + iVar14 * iVar8;
  *(int *)(puVar15 + 0xc) = iVar10;
  *(int *)(puVar15 + 0x54) = iVar10 + iVar21 * iVar8;
  FUN_1001b4c8(iVar20,0);
  memw();
  iVar10 = *(int *)puVar4;
  iVar8 = *(int *)PTR_DAT_10006838;
  iVar20 = *(int *)(puVar15 + 0xb8) * 8;
  *(int *)(puVar15 + 0x10) = iVar8;
  iVar8 = iVar8 + iVar10 * iVar20;
  memw();
  iVar10 = *(int *)puVar4;
  *(int *)(puVar15 + 0x14) = iVar8;
  memw();
  iVar14 = *(int *)puVar4;
  iVar8 = iVar8 + iVar10 * iVar20;
  *(int *)(puVar15 + 0x18) = iVar8;
  *(int *)(puVar15 + 0x1c) = iVar8 + iVar14 * iVar20;
  *(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26);
  *(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26);
  *(uint *)(puVar15 + 0xec) = (uint)*(ushort *)(param_1 + 0x32);
  *(uint *)(puVar15 + 0xe8) = (uint)*(ushort *)(param_1 + 0x30);
  if (*(char *)(param_1 + 0x74) == '\0') {
    uVar7 = *(uint *)(puVar15 + 0xfc) & DAT_1000628c;
  }
  else {
    uVar7 = *(uint *)(puVar15 + 0xfc) | DAT_10005e34;
  }
  *(uint *)(puVar15 + 0xfc) = uVar7;
  puVar2 = DAT_1000680c;
  memw();
  memw();
  *DAT_10006808 = *DAT_10006808 & 0xfffffeff;
  puVar1 = DAT_100067c0;
  memw();
  memw();
  *puVar2 = *puVar2 & 0xfffffeff;
  puVar3 = DAT_1000680c;
  puVar2 = DAT_10006808;
  uVar7 = DAT_100063a0;
  memw();
  uVar19 = *puVar1;
  while ((uVar19 & 0x200) != 0) {
    memw();
    uVar19 = *puVar1;
  }
  do {
    memw();
  } while ((*DAT_100067d8 & 0x200) != 0);
  memw();
  memw();
  *DAT_10006808 = *DAT_10006808 & DAT_100063a0;
  memw();
  memw();
  *puVar3 = *puVar3 & uVar7;
  uVar7 = DAT_10006850;
  memw();
  memw();
  *puVar2 = *puVar2 & DAT_10006850;
  memw();
  iVar8 = *(int *)PTR_DAT_100067c8;
  memw();
  *puVar3 = *puVar3 & uVar7;
  puVar12 = DAT_10006874;
  if (iVar8 == 0) {
    if (*(short *)(param_1 + 0x14) == 300) {
      uVar6 = DAT_1000685c;
      if (iVar5 == 0) {
        uVar6 = DAT_10006858;
      }
    }
    else {
      uVar6 = DAT_10006864;
      if (iVar5 == 0) {
        uVar6 = DAT_10006860;
      }
    }
    memw();
    *DAT_10006854 = uVar6;
    uVar6 = 0x62;
    if (iVar5 == 0) {
      uVar6 = 0xe5;
    }
    memw();
    *DAT_10006868 = uVar6;
  }
  else if (iVar8 == 1) {
    if (*(short *)(param_1 + 0x14) == 300) {
      uVar6 = DAT_10006870;
      if (iVar5 == 0) {
        uVar6 = DAT_1000686c;
      }
      memw();
      *DAT_10006854 = uVar6;
      uVar6 = DAT_10006870;
      if (iVar5 == 0) {
        uVar6 = DAT_1000686c;
      }
    }
    else {
      uVar6 = DAT_1000687c;
      if (iVar5 == 0) {
        uVar6 = DAT_10006878;
      }
      memw();
      *DAT_10006854 = uVar6;
      uVar6 = DAT_1000687c;
      if (iVar5 == 0) {
        uVar6 = DAT_10006878;
      }
    }
    memw();
    *puVar12 = uVar6;
    uVar6 = 0x62;
    uVar16 = 0x62;
    if (iVar5 == 0) {
      uVar6 = 0xe5;
    }
    memw();
    *DAT_10006868 = uVar6;
    if (iVar5 == 0) {
      uVar16 = 0xe5;
    }
    memw();
    *DAT_10006880 = uVar16;
  }
  puVar1 = DAT_10006884;
  memw();
  *DAT_100067c0 = 0;
  puVar2 = DAT_1000688c;
  memw();
  *DAT_100067d8 = 0;
  memw();
  uVar19 = DAT_10006888 ^ 0xffffffff;
  memw();
  *puVar1 = *puVar1 & uVar19 | 0x100;
  memw();
  uVar7 = *puVar2;
  *(undefined4 *)(PTR_DAT_10006770 + 0xe4) = 1;
  iVar8 = *(int *)PTR_DAT_100067c8;
  memw();
  *puVar2 = uVar7 & uVar19 | 0x100;
  puVar2 = DAT_1000688c;
  puVar1 = DAT_10006884;
  if (iVar8 == 0) {
    local_30 = 5;
    uVar7 = 0xc;
LAB_10014d64:
    if (iVar5 == 0) {
      local_30 = uVar7;
    }
  }
  else if (iVar8 == 1) {
    local_30 = 8;
    uVar7 = 0x15;
    goto LAB_10014d64;
  }
  memw();
  memw();
  *DAT_10006884 = *DAT_10006884 & 0xffffffc0 | local_30;
  memw();
  memw();
  *puVar2 = *puVar2 & 0xffffffc0 | local_30;
  memw();
  uVar7 = DAT_10006890 ^ 0xffffffff;
  memw();
  *puVar1 = *puVar1 & uVar7;
  memw();
  memw();
  *puVar2 = *puVar2 & uVar7 | DAT_1000637c;
  uVar7 = DAT_10005c8c;
  memw();
  memw();
  *puVar1 = *puVar1 | DAT_10005c8c;
  memw();
  memw();
  *puVar2 = *puVar2 | uVar7;
  puVar15 = PTR_DAT_10006840;
  memw();
  *(undefined4 *)PTR_DAT_10006840 = 0;
  puVar12 = DAT_10006894;
  memw();
  uVar19 = *(uint *)puVar15;
  puVar1 = DAT_1000680c;
  uVar7 = DAT_10006898;
  while (DAT_1000680c = puVar1, DAT_10006898 = uVar7, uVar19 < 0x10) {
    memw();
    memw();
    puVar12[*(int *)puVar15 * 4] = 0;
    memw();
    memw();
    *(int *)puVar15 = *(int *)puVar15 + 1;
    memw();
    puVar1 = DAT_1000680c;
    uVar7 = DAT_10006898;
    uVar19 = *(uint *)puVar15;
  }
  iVar5 = *(int *)(PTR_DAT_10006770 + 200);
  if (iVar5 == 1) {
    memw();
    memw();
    *DAT_10006808 = *DAT_10006808 & uVar7;
    memw();
    memw();
    *puVar1 = *puVar1 & uVar7;
  }
  else {
    uVar7 = DAT_10005c88;
    if ((iVar5 == 2) || (uVar7 = DAT_10005c84, iVar5 == 4)) {
      memw();
      uVar19 = DAT_1000689c ^ 0xffffffff;
      memw();
      *DAT_10006808 = *DAT_10006808 & uVar19 | uVar7;
      memw();
      memw();
      *puVar1 = *puVar1 & uVar19 | uVar7;
    }
  }
  puVar9 = PTR_DAT_100068ac;
  puVar12 = DAT_100068a4;
  puVar15 = PTR_DAT_10006840;
  if (*(short *)(param_1 + 0x22) == 1) {
    sVar18 = *(short *)(param_1 + 0x14);
    if (sVar18 == 300) {
      puVar15 = PTR_DAT_100068a8;
      if ((*(int *)PTR_DAT_100067c8 != 0) ||
         (puVar12 = (undefined4 *)PTR_DAT_100068a0, *(int *)(PTR_DAT_10006770 + 0xec) == 0)) {
LAB_10014f36:
        puVar12 = (undefined4 *)(puVar15 + *(int *)PTR_DAT_100067c8 * 8);
      }
      uVar16 = *puVar12;
      uVar6 = puVar12[1];
      puVar12 = DAT_100068a4;
      puVar11 = DAT_10006894;
    }
    else {
      if (sVar18 != 600) {
        if (sVar18 == 0x4b0) {
          memw();
          *(undefined4 *)PTR_DAT_10006840 = 0;
          puVar4 = PTR_DAT_100068c4;
          puVar9 = PTR_DAT_100068c0;
          puVar12 = DAT_10006894;
          memw();
          uVar7 = *(uint *)puVar15;
          while (uVar7 < 0x10) {
            if ((*puVar9 & 0xf0) == 0) {
              memw();
              memw();
              memw();
              puVar12[*(int *)puVar15 * 4] = *(undefined4 *)(puVar4 + *(int *)puVar15 * 4);
            }
            memw();
            memw();
            *(int *)puVar15 = *(int *)puVar15 + 1;
            memw();
            uVar7 = *(uint *)puVar15;
          }
        }
        goto LAB_1001506d;
      }
      if ((*(int *)PTR_DAT_100067c8 == 0) && (*(int *)(PTR_DAT_10006770 + 0xec) != 0)) {
        uVar6 = *(undefined4 *)(PTR_DAT_100068ac + 4);
        memw();
        *DAT_10006894 = *(undefined4 *)PTR_DAT_100068ac;
        memw();
        *puVar12 = uVar6;
        uVar16 = *(undefined4 *)(puVar9 + 8);
        uVar6 = *(undefined4 *)(puVar9 + 0xc);
        puVar12 = DAT_100068b4;
        puVar11 = DAT_100068b0;
      }
      else {
        puVar15 = PTR_DAT_100068bc;
        if (*(int *)(PTR_DAT_10006770 + 200) != 2) goto LAB_10014f36;
        puVar11 = (undefined4 *)(PTR_DAT_100068b8 + *(int *)PTR_DAT_100067c8 * 0x10);
        uVar6 = puVar11[1];
        memw();
        *DAT_10006894 = *puVar11;
        memw();
        *puVar12 = uVar6;
        uVar16 = puVar11[2];
        uVar6 = puVar11[3];
        puVar12 = DAT_100068b4;
        puVar11 = DAT_100068b0;
      }
    }
    memw();
    *puVar11 = uVar16;
    memw();
    *puVar12 = uVar6;
  }
  else if (*(short *)(param_1 + 0x22) == 2) {
    if ((*(int *)PTR_DAT_100067c8 == 0) && (*(int *)(PTR_DAT_10006770 + 0xec) != 0)) {
      memw();
      *(undefined4 *)PTR_DAT_10006840 = 0;
      puVar9 = PTR_DAT_100068c8;
      puVar12 = DAT_10006894;
      memw();
      uVar7 = *(uint *)puVar15;
      while (uVar7 < 4) {
        memw();
        memw();
        memw();
        puVar12[*(int *)puVar15 * 4] = *(undefined4 *)(puVar9 + *(int *)puVar15 * 4);
        memw();
        memw();
        *(int *)puVar15 = *(int *)puVar15 + 1;
        memw();
        uVar7 = *(uint *)puVar15;
      }
    }
    else {
      memw();
      *(undefined4 *)PTR_DAT_10006840 = 0;
      puVar4 = PTR_DAT_100068cc;
      puVar12 = DAT_10006894;
      puVar9 = PTR_DAT_100067c8;
      memw();
      uVar7 = *(uint *)puVar15;
      while (uVar7 < 4) {
        memw();
        memw();
        memw();
        puVar12[*(int *)puVar15 * 4] =
             *(undefined4 *)(puVar4 + *(int *)puVar15 * 4 + *(int *)puVar9 * 0x10);
        memw();
        memw();
        *(int *)puVar15 = *(int *)puVar15 + 1;
        memw();
        uVar7 = *(uint *)puVar15;
      }
    }
  }
LAB_1001506d:
  puVar2 = DAT_1000680c;
  puVar1 = DAT_10006808;
  memw();
  memw();
  *DAT_10006808 = *DAT_10006808 & 0xffffffcf;
  memw();
  memw();
  *puVar2 = *puVar2 & 0xffffffcf;
  if (*(short *)(param_1 + 0x16) == 300) {
    memw();
    uVar7 = *puVar1;
    uVar19 = 0x10;
LAB_100150b2:
    memw();
    *puVar1 = uVar7 & 0xffffffcf | uVar19;
    memw();
    memw();
    *puVar2 = *puVar2 & 0xffffffcf | uVar19;
  }
  else if (*(short *)(param_1 + 0x16) == 0x96) {
    memw();
    uVar7 = *puVar1;
    uVar19 = 0x20;
    goto LAB_100150b2;
  }
  puVar1 = DAT_1000680c;
  puVar15 = PTR_DAT_100067c8;
  uVar7 = DAT_10005f20;
  if (*(int *)PTR_DAT_100067c8 == 1) {
    memw();
    uVar19 = DAT_10005eb4 ^ 0xffffffff;
    memw();
    *DAT_10006808 = *DAT_10006808 & uVar19 | DAT_10005f20;
    memw();
    memw();
    *puVar1 = *puVar1 & uVar19 | uVar7;
  }
  if (*(int *)puVar15 == 0) {
    uStack_2c = 0x68;
    sVar18 = *(short *)(param_1 + 0x14);
    if (sVar18 != 600) {
LAB_10015158:
      if (sVar18 == 300) {
        *(ushort *)(param_1 + 0x18) = 0x69a - (*(ushort *)(param_1 + 0x24) >> 1);
      }
      goto LAB_1001516d;
    }
    uVar13 = *(ushort *)(param_1 + 0x24);
    sVar17 = (short)DAT_100068d0;
LAB_1001514c:
    uVar13 = uVar13 >> 1;
  }
  else {
    if (*(int *)puVar15 != 1) goto LAB_1001516d;
    uStack_2c = 0x1e;
    sVar18 = *(short *)(param_1 + 0x14);
    sVar17 = (short)DAT_100068d4;
    if (sVar18 != 0x4b0) {
      if (sVar18 != 600) goto LAB_10015158;
      uVar13 = *(ushort *)(param_1 + 0x24);
      goto LAB_1001514c;
    }
    uVar13 = *(ushort *)(param_1 + 0x24) >> 2;
  }
  *(ushort *)(param_1 + 0x18) = sVar17 - uVar13;
LAB_1001516d:
  puVar1 = DAT_100068e0;
  puVar15 = PTR_DAT_10006770;
  memw();
  memw();
  *DAT_100068d8 = (uint)*(ushort *)(param_1 + 0x18) << 0x10 | uStack_2c;
  memw();
  memw();
  *DAT_100068dc = (uint)*(ushort *)(param_1 + 0x18) << 0x10 | uStack_2c;
  puVar2 = DAT_100068e8;
  memw();
  uVar19 = (uint)*(ushort *)(puVar15 + 0xbe);
  uVar7 = DAT_100068e4 ^ 0xffffffff;
  memw();
  *puVar1 = *puVar1 & uVar7 | uVar19;
  puVar1 = DAT_10006808;
  memw();
  memw();
  *puVar2 = *puVar2 & uVar7 | uVar19;
  memw();
  iVar5 = *(int *)PTR_DAT_100067c8;
  memw();
  *puVar1 = *puVar1 | 0x100;
  if (iVar5 == 1) {
    memw();
    memw();
    *DAT_1000680c = *DAT_1000680c | 0x100;
  }
  *(undefined4 *)(puVar15 + 0x6c) = 1;
  FUN_10017184(10);
  return 0;
}


