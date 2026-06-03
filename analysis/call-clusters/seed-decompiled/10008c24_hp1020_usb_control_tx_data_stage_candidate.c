/* Function: 10008c24 hp1020_usb_control_tx_data_stage_candidate */


undefined4 hp1020_usb_control_tx_data_stage_candidate(void)

{
  undefined *puVar1;
  undefined *puVar2;
  uint *puVar3;
  undefined *puVar4;
  undefined *puVar5;
  uint *puVar6;
  uint uVar7;
  int iVar8;
  uint uVar9;
  undefined4 uVar10;
  undefined1 *puVar11;
  uint uVar12;
  int iVar13;
  undefined4 uVar14;
  int iVar15;
  int iVar16;
  undefined1 auStack_30 [48];
  
  puVar3 = DAT_10005e90;
  uVar10 = *(undefined4 *)(PTR_DAT_10005e1c + 0x40);
  uVar14 = *(undefined4 *)(PTR_DAT_10005e1c + 0x3c);
  memw();
  memw();
  *DAT_10005e90 = *DAT_10005e90 | 2;
  FUN_100173c8(uVar10,uVar14);
  puVar4 = PTR_DAT_10005e94;
  puVar1 = PTR_DAT_10005e1c;
  memw();
  uVar7 = *puVar3;
  while ((uVar7 & 2) != 0) {
    memw();
    uVar7 = *puVar3;
  }
  FUN_1001b38c(*(undefined4 *)PTR_DAT_10005e94,*(undefined4 *)(PTR_DAT_10005e1c + 0x40),
               *(undefined4 *)(PTR_DAT_10005e1c + 0x3c));
  puVar6 = DAT_10005e9c;
  puVar5 = PTR_DAT_10005e98;
  if (*(int *)(puVar1 + 0x3c) == 0) {
    uVar10 = *(undefined4 *)puVar4;
    memw();
    iVar8 = *(int *)PTR_DAT_10005e98;
    *(char *)(iVar8 + 8) = (char)((uint)uVar10 >> 0x18);
    *(char *)(iVar8 + 9) = (char)((uint)uVar10 >> 0x10);
    *(char *)(iVar8 + 10) = (char)((uint)uVar10 >> 8);
    *(char *)(iVar8 + 0xb) = (char)uVar10;
    iVar8 = *(int *)puVar5;
    *(undefined1 *)(iVar8 + 4) = 0;
    *(undefined1 *)(iVar8 + 5) = 0;
    *(undefined1 *)(iVar8 + 6) = 0;
    *(undefined1 *)(iVar8 + 7) = 0;
    iVar8 = *(int *)puVar5;
    *(undefined1 *)(iVar8 + 0xc) = 0;
    *(undefined1 *)(iVar8 + 0xd) = 0;
    *(undefined1 *)(iVar8 + 0xe) = 0;
    *(undefined1 *)(iVar8 + 0xf) = 0;
    puVar11 = *(undefined1 **)puVar5;
    memw();
    iVar8 = *(int *)(puVar1 + 0x3c) + DAT_10005e80;
    memw();
    *puVar11 = (char)((uint)iVar8 >> 0x18);
    memw();
    memw();
    puVar11[1] = (char)((uint)iVar8 >> 0x10);
    memw();
    memw();
    puVar11[2] = (char)((uint)iVar8 >> 8);
    memw();
    memw();
    puVar11[3] = (char)iVar8;
    *(undefined4 *)(puVar1 + 0x3c) = 0;
    memw();
    *DAT_10005ea0 = *(undefined4 *)puVar5;
    puVar1 = PTR_DAT_10005e18;
    memw();
    memw();
    *puVar3 = *puVar3 | 0x108;
    threadx_queue_receive_candidate(puVar1,1,1,auStack_30,0xffffffff);
  }
  else {
    do {
      memw();
      uVar7 = 0;
      if (*puVar6 < *(uint *)(puVar1 + 0x3c)) {
        iVar8 = 0x10;
        do {
          if (4 < uVar7) break;
          memw();
          iVar15 = uVar7 * 0x10;
          iVar16 = iVar15 + *(int *)puVar5;
          iVar13 = *(int *)puVar4 + uVar7 * *puVar6;
          *(char *)(iVar16 + 8) = (char)((uint)iVar13 >> 0x18);
          *(char *)(iVar16 + 9) = (char)((uint)iVar13 >> 0x10);
          *(char *)(iVar16 + 10) = (char)((uint)iVar13 >> 8);
          *(char *)(iVar16 + 0xb) = (char)iVar13;
          memw();
          uVar12 = *puVar6;
          puVar11 = (undefined1 *)(iVar15 + *(int *)puVar5);
          memw();
          memw();
          *puVar11 = (char)(uVar12 >> 0x18);
          memw();
          memw();
          puVar11[1] = (char)(uVar12 >> 0x10);
          memw();
          memw();
          puVar11[2] = (char)(uVar12 >> 8);
          memw();
          memw();
          puVar11[3] = (char)uVar12;
          iVar13 = iVar15 + *(int *)puVar5;
          *(undefined1 *)(iVar13 + 4) = 0;
          *(undefined1 *)(iVar13 + 5) = 0;
          *(undefined1 *)(iVar13 + 6) = 0;
          *(undefined1 *)(iVar13 + 7) = 0;
          iVar15 = iVar15 + *(int *)puVar5;
          iVar13 = *(int *)puVar5 + iVar8;
          *(char *)(iVar15 + 0xc) = (char)((uint)iVar13 >> 0x18);
          *(char *)(iVar15 + 0xd) = (char)((uint)iVar13 >> 0x10);
          *(char *)(iVar15 + 0xe) = (char)((uint)iVar13 >> 8);
          *(char *)(iVar15 + 0xf) = (char)iVar13;
          iVar13 = *(int *)(puVar1 + 0x3c);
          memw();
          uVar12 = *puVar6;
          uVar7 = uVar7 + 1;
          memw();
          uVar9 = *puVar6;
          iVar8 = iVar8 + 0x10;
          *(uint *)(puVar1 + 0x3c) = iVar13 - uVar12;
        } while (uVar9 < iVar13 - uVar12);
      }
      if (uVar7 == 5) {
        iVar8 = *(int *)puVar5;
        memw();
        uVar7 = (uint)*(byte *)(iVar8 + 0x43) |
                (uint)*(byte *)(iVar8 + 0x42) << 8 |
                (uint)*(byte *)(iVar8 + 0x41) << 0x10 | (uint)*(byte *)(iVar8 + 0x40) << 0x18 |
                DAT_10005e80;
        memw();
        *(byte *)(iVar8 + 0x40) = (byte)(uVar7 >> 0x18);
        memw();
        memw();
        *(char *)(iVar8 + 0x41) = (char)(uVar7 >> 0x10);
        memw();
        memw();
        *(char *)(iVar8 + 0x42) = (char)(uVar7 >> 8);
        memw();
        memw();
        *(char *)(iVar8 + 0x43) = (char)uVar7;
      }
      else {
        memw();
        iVar16 = uVar7 * 0x10;
        iVar13 = iVar16 + *(int *)puVar5;
        iVar8 = *(int *)puVar4 + uVar7 * *puVar6;
        *(char *)(iVar13 + 8) = (char)((uint)iVar8 >> 0x18);
        *(char *)(iVar13 + 9) = (char)((uint)iVar8 >> 0x10);
        *(char *)(iVar13 + 10) = (char)((uint)iVar8 >> 8);
        *(char *)(iVar13 + 0xb) = (char)iVar8;
        iVar8 = iVar16 + *(int *)puVar5;
        *(undefined1 *)(iVar8 + 4) = 0;
        *(undefined1 *)(iVar8 + 5) = 0;
        *(undefined1 *)(iVar8 + 6) = 0;
        *(undefined1 *)(iVar8 + 7) = 0;
        iVar8 = iVar16 + *(int *)puVar5;
        *(undefined1 *)(iVar8 + 0xc) = 0;
        *(undefined1 *)(iVar8 + 0xd) = 0;
        *(undefined1 *)(iVar8 + 0xe) = 0;
        *(undefined1 *)(iVar8 + 0xf) = 0;
        puVar11 = (undefined1 *)(iVar16 + *(int *)puVar5);
        memw();
        iVar8 = *(int *)(puVar1 + 0x3c) + DAT_10005e80;
        memw();
        *puVar11 = (char)((uint)iVar8 >> 0x18);
        memw();
        memw();
        puVar11[1] = (char)((uint)iVar8 >> 0x10);
        memw();
        memw();
        puVar11[2] = (char)((uint)iVar8 >> 8);
        memw();
        memw();
        puVar11[3] = (char)iVar8;
        *(undefined4 *)(puVar1 + 0x3c) = 0;
      }
      puVar2 = PTR_DAT_10005e18;
      memw();
      *DAT_10005ea0 = *(undefined4 *)puVar5;
      memw();
      memw();
      *puVar3 = *puVar3 | 0x108;
      threadx_queue_receive_candidate(puVar2,1,1,auStack_30,0xffffffff);
    } while (*(int *)(puVar1 + 0x3c) != 0);
  }
  return *(undefined4 *)(PTR_DAT_10005e1c + 0x3c);
}


