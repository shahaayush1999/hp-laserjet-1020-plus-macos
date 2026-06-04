/* Function: 10008ff0 hp1020_usb2_thread */


void hp1020_usb2_thread(void)

{
  undefined1 uVar1;
  undefined1 uVar2;
  ushort uVar3;
  uint *puVar4;
  undefined *puVar5;
  uint *puVar6;
  undefined *puVar7;
  undefined *puVar8;
  uint *puVar9;
  undefined4 *puVar10;
  undefined4 uVar11;
  bool bVar12;
  undefined4 uVar13;
  undefined4 *puVar14;
  undefined1 *puVar15;
  uint uVar16;
  int *piVar17;
  int iVar18;
  byte *pbVar19;
  ushort *puVar20;
  undefined4 uStack_70;
  undefined4 uStack_6c;
  undefined *puStack_68;
  undefined *puStack_64;
  undefined4 uStack_60;
  undefined4 uStack_5c;
  undefined1 auStack_50 [16];
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined1 uStack_30;
  undefined1 uStack_2f;
  undefined1 auStack_2e [46];
  
  FUN_1001214c();
  puVar6 = DAT_10005eac;
  memw();
  if ((*DAT_10005eac & 1) == 0) {
    memw();
    memw();
    *DAT_10005eac = *DAT_10005eac | 2;
    puVar4 = DAT_10005df4;
    memw();
    memw();
    *puVar6 = *puVar6 & 0xfffffffd;
    puVar9 = DAT_10005ea8;
    memw();
    memw();
    *puVar4 = *puVar4 | 8;
    memw();
    memw();
    *puVar9 = *puVar9 & DAT_10005eb0;
    puVar6 = DAT_10005e90;
    memw();
    memw();
    *puVar9 = *puVar9 | DAT_10005eb4;
    memw();
    memw();
    *puVar9 = *puVar9 | 800;
    memw();
    uVar16 = *puVar6;
    *DAT_10005e88 = *DAT_10005e88 | 0x20;
    memw();
    *puVar6 = uVar16;
    puVar6 = DAT_10005e24;
    memw();
    uVar16 = *DAT_10005e24;
    *DAT_10005e70 = *DAT_10005e70 | 0x22;
    puVar4 = DAT_10005eb8;
    memw();
    *puVar6 = uVar16 | 2;
    puVar14 = DAT_10005ebc;
    uVar13 = DAT_10005c84;
    memw();
    memw();
    *puVar4 = *puVar4 | 0x77;
    memw();
    *puVar14 = uVar13;
    puVar10 = DAT_10005ed0;
    puVar14 = DAT_10005ec8;
    memw();
    *DAT_10005ec0 = PTR_DAT_10005ec4;
    puVar5 = PTR_DAT_10005ed4;
    memw();
    *puVar14 = PTR_LAB_10005ecc;
    memw();
    *puVar10 = puVar5;
    memw();
    *DAT_10005ed8 = 0x10;
    memw();
    *DAT_10005edc = 0x40;
    uVar13 = 0x200;
    puVar14 = (undefined4 *)PTR_DAT_10005e50;
  }
  else {
    memw();
    *(undefined4 *)PTR_DAT_10005e50 = *DAT_10005ee0;
    memw();
    *DAT_10005ed8 = 0x10;
    uVar13 = 0x40;
    puVar14 = DAT_10005edc;
  }
  memw();
  *puVar14 = uVar13;
  puVar5 = PTR_DAT_10005ee8;
  memw();
  *DAT_10005ee4 = 0x40;
  puVar14 = *(undefined4 **)puVar5;
  memw();
  *puVar14 = 0;
  puVar14[1] = 0;
  puVar7 = PTR_DAT_10005eec;
  uVar13 = *(undefined4 *)PTR_DAT_10005ef0;
  iVar18 = *(int *)PTR_DAT_10005eec;
  *(char *)(iVar18 + 8) = (char)((uint)uVar13 >> 0x18);
  *(char *)(iVar18 + 9) = (char)((uint)uVar13 >> 0x10);
  *(char *)(iVar18 + 10) = (char)((uint)uVar13 >> 8);
  *(char *)(iVar18 + 0xb) = (char)uVar13;
  iVar18 = *(int *)puVar7;
  *(undefined1 *)(iVar18 + 4) = 0;
  *(undefined1 *)(iVar18 + 5) = 0;
  *(undefined1 *)(iVar18 + 6) = 0;
  *(undefined1 *)(iVar18 + 7) = 0;
  iVar18 = *(int *)puVar7;
  *(undefined1 *)(iVar18 + 0xc) = 0;
  *(undefined1 *)(iVar18 + 0xd) = 0;
  *(undefined1 *)(iVar18 + 0xe) = 0;
  *(undefined1 *)(iVar18 + 0xf) = 0;
  puVar15 = *(undefined1 **)puVar7;
  memw();
  memw();
  *puVar15 = 8;
  memw();
  memw();
  puVar15[1] = 0;
  memw();
  memw();
  puVar15[2] = 0;
  memw();
  memw();
  puVar15[3] = 0;
  memw();
  *DAT_10005ef4 = *(undefined4 *)puVar5;
  puVar14 = DAT_10005e9c;
  uStack_60 = 0;
  uStack_70 = 1;
  uStack_6c = 0;
  uStack_5c = 1;
  memw();
  *DAT_10005ef8 = *(undefined4 *)puVar7;
  memw();
  *puVar14 = 0x40;
  memw();
  *DAT_10005ed8 = 0x10;
  puStack_68 = PTR_LAB_10005efc;
  puStack_64 = PTR_LAB_10005f00;
  uVar11 = FUN_10007c00(&uStack_70);
  uVar13 = DAT_10005f04;
  puVar7 = PTR_DAT_10005e2c;
  puVar5 = PTR_DAT_10005e1c;
  *(undefined4 *)PTR_DAT_10005e1c = uVar11;
  puVar15 = *(undefined1 **)puVar7;
  memw();
  *DAT_10005e00 = uVar13;
  memw();
  memw();
  *puVar15 = 8;
  memw();
  memw();
  puVar15[1] = 0;
  memw();
  memw();
  puVar15[2] = 0;
  puVar8 = PTR_DAT_10005e44;
  memw();
  memw();
  puVar15[3] = 0;
  uVar13 = *(undefined4 *)puVar8;
  iVar18 = *(int *)puVar7;
  *(char *)(iVar18 + 8) = (char)((uint)uVar13 >> 0x18);
  *(char *)(iVar18 + 9) = (char)((uint)uVar13 >> 0x10);
  *(char *)(iVar18 + 10) = (char)((uint)uVar13 >> 8);
  *(char *)(iVar18 + 0xb) = (char)uVar13;
  puVar14 = DAT_10005f08;
  iVar18 = *(int *)puVar7;
  memw();
  *DAT_10005e60 = iVar18;
  *(undefined1 *)(iVar18 + 0xc) = 0;
  *(undefined1 *)(iVar18 + 0xd) = 0;
  *(undefined1 *)(iVar18 + 0xe) = 0;
  *(undefined1 *)(iVar18 + 0xf) = 0;
  puVar7 = PTR_DAT_10005e98;
  puVar15 = *(undefined1 **)PTR_DAT_10005e98;
  memw();
  *puVar14 = *(undefined4 *)PTR_DAT_10005e50;
  memw();
  memw();
  *puVar15 = 0xc0;
  memw();
  memw();
  puVar15[1] = 0;
  memw();
  memw();
  puVar15[2] = 0;
  memw();
  memw();
  puVar15[3] = 0;
  puVar4 = DAT_10005eac;
  memw();
  *DAT_10005ea0 = *(int *)puVar7 + DAT_10005e34;
  memw();
  memw();
  *puVar4 = *puVar4 | 4;
  puVar6 = DAT_10005ea8;
  memw();
  memw();
  *puVar4 = *puVar4 | 1;
  puVar7 = PTR_LAB_10005f0c;
  memw();
  uVar16 = *puVar6;
  *PTR_DAT_10005e20 = 1;
  memw();
  *puVar6 = uVar16 | 8;
  FUN_1001716c(4,puVar7);
  puVar6 = DAT_10005e24;
  memw();
  memw();
  *DAT_10005e70 = *DAT_10005e70 | 0x100;
  memw();
  memw();
  *puVar6 = *puVar6 | 0x100;
  FUN_10017184(4);
  FUN_10018274(PTR_DAT_10005f10,PTR_s_USB2IdleThread_10005f14,PTR_DAT_10005f18,0,PTR_DAT_10005f1c,
               0x200,0x1f,0x1f,10,1);
  bVar12 = false;
  do {
    FUN_10017d28(PTR_DAT_10005e18,DAT_10005f20,1,auStack_50,0xffffffff);
    memw();
    pbVar19 = (byte *)*DAT_10005ef4;
    uVar16 = (uint)pbVar19[3] |
             (uint)pbVar19[2] << 8 | (uint)pbVar19[1] << 0x10 | (uint)*pbVar19 << 0x18;
    if (((uVar16 & DAT_10005e30) == DAT_10005e34) && ((uVar16 & DAT_10005f24) == 0)) {
      iVar18 = *(int *)PTR_DAT_10005ee8;
      uVar1 = *(undefined1 *)(iVar18 + 0xe);
      memw();
      memw();
      *(undefined1 *)(iVar18 + 0xe) = *(undefined1 *)(iVar18 + 0xf);
      memw();
      memw();
      *(undefined1 *)(iVar18 + 0xf) = uVar1;
      uVar1 = *(undefined1 *)(iVar18 + 0xc);
      memw();
      uVar2 = *(undefined1 *)(iVar18 + 0xc);
      memw();
      *(undefined1 *)(iVar18 + 0xc) = *(undefined1 *)(iVar18 + 0xd);
      memw();
      memw();
      *(undefined1 *)(iVar18 + 0xd) = uVar1;
      uVar16 = (uint)*(ushort *)(iVar18 + 8);
      if (uVar16 == DAT_10005f80) {
        puVar20 = *(ushort **)PTR_DAT_10005f68;
        *(ushort **)(puVar5 + 0x40) = puVar20;
        if (*(ushort *)(iVar18 + 0xe) < *puVar20) {
          uVar3 = *(ushort *)(iVar18 + 0xe);
        }
        else {
          uVar3 = *puVar20;
        }
        *(uint *)(puVar5 + 0x3c) = (uint)uVar3;
        FUN_10008c24();
        *PTR_DAT_10005df0 = 0;
        uVar16 = FUN_10011178(0x19);
        if ((uVar16 & DAT_10005c88) == 0) {
          if (((uVar16 & DAT_10005f74) == DAT_10005f78) || ((uVar16 & DAT_10005f74) == DAT_10005f7c)
             ) {
            uStack_40 = 0x1a;
            uVar13 = 0;
            uStack_3c = 0;
            uStack_38 = 0;
            uStack_34 = 0;
            goto LAB_100097e9;
          }
        }
        else if (((uVar16 & 0xffff) + DAT_10005f6c < 2) || ((uVar16 & 0xffff) == DAT_10005f70)) {
          uStack_40 = 0x32;
          uStack_3c = 1;
          uVar13 = 10;
LAB_100097e9:
          hp1020_queue_send_candidate(uVar13,&uStack_40);
        }
      }
      else {
        if ((int)DAT_10005f80 < (int)uVar16) {
          if (uVar16 == DAT_10005f8c) {
            if (*(short *)(iVar18 + 10) == 0) {
              uStack_2f = *(undefined1 *)(iVar18 + 0xb);
              puVar15 = &uStack_2f;
              goto LAB_1000984f;
            }
          }
          else if ((int)DAT_10005f8c < (int)uVar16) {
            if (uVar16 == DAT_10005f94) {
              piVar17 = *(int **)PTR_DAT_10005e10;
              auStack_2e[0] = 0;
              for (; piVar17 != (int *)0x0; piVar17 = (int *)*piVar17) {
                if (*(int *)(piVar17[3] + 0xc) == 0) {
                  auStack_2e[0] = 1;
                  break;
                }
              }
              puVar15 = auStack_2e;
              goto LAB_1000984f;
            }
          }
          else if (uVar16 == DAT_10005f90) {
            uStack_30 = 0;
            puVar15 = &uStack_30;
LAB_1000984f:
            *(undefined1 **)(puVar5 + 0x40) = puVar15;
            *(undefined4 *)(puVar5 + 0x3c) = 1;
            goto LAB_100096a9;
          }
        }
        else {
          if (uVar16 == DAT_10005f84) {
            FUN_10007c70(*(undefined4 *)puVar5,uVar2);
            FUN_10008fb0();
            *(undefined4 *)(puVar5 + 0x3c) = 0;
LAB_100096a9:
            FUN_10008c24();
            goto LAB_1000985c;
          }
          if ((uVar16 == DAT_10005f88) && (uVar16 = *(byte *)(iVar18 + 0xb) - 1, uVar16 < 7)) {
                    /* WARNING: Could not recover jumptable at 0x10009473. Too many branches */
                    /* WARNING: Treating indirect jump as call */
            (**(code **)(PTR_switchdataD_10003500_10005f64 + uVar16 * 4))();
            return;
          }
        }
        bVar12 = true;
      }
LAB_1000985c:
      puVar6 = DAT_10005e90;
      if (bVar12) {
        memw();
        memw();
        *DAT_10005e24 = *DAT_10005e24 | 1;
        memw();
        memw();
        *puVar6 = *puVar6 | 1;
        bVar12 = false;
      }
      memw();
      **(undefined4 **)PTR_DAT_10005ee8 = 0;
    }
    memw();
    pbVar19 = (byte *)*DAT_10005ef8;
    if ((((uint)pbVar19[3] |
         (uint)pbVar19[2] << 8 | (uint)pbVar19[1] << 0x10 | (uint)*pbVar19 << 0x18) & DAT_10005e30)
        == DAT_10005e34) {
      puVar15 = *(undefined1 **)PTR_DAT_10005eec;
      memw();
      memw();
      *puVar15 = 8;
      memw();
      memw();
      puVar15[1] = 0;
      memw();
      memw();
      puVar15[2] = 0;
      memw();
      memw();
      puVar15[3] = 0;
    }
    memw();
    uVar16 = *(uint *)PTR_DAT_10005e38;
    memw();
    *DAT_10005e24 = *DAT_10005e24 | 0x100;
    if (uVar16 < 0x201) {
      memw();
      memw();
      *DAT_10005e70 = *DAT_10005e70 | 0x100;
    }
    *PTR_DAT_10005e64 = 0;
  } while( true );
}

