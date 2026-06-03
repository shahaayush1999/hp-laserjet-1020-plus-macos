/* Function: 1000a334 hp1020_task_entry_1000a334 */


/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Type propagation algorithm not settling */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 hp1020_task_entry_1000a334(int param_1)

{
  ushort *puVar1;
  ushort uVar2;
  short sVar3;
  undefined *puVar4;
  undefined *puVar5;
  undefined *puVar6;
  undefined *puVar7;
  undefined *puVar8;
  undefined *puVar9;
  uint uVar10;
  int iVar11;
  uint uVar12;
  int iVar13;
  int iVar14;
  undefined *puVar15;
  undefined4 *puVar16;
  int iVar17;
  undefined2 uVar18;
  uint uVar19;
  undefined4 *puVar20;
  undefined4 uVar21;
  uint uVar22;
  undefined4 uVar23;
  undefined1 in_b7;
  undefined1 auStack_a0 [16];
  undefined4 uStack_90;
  undefined4 uStack_8c;
  undefined4 uStack_88;
  undefined4 uStack_80;
  undefined1 auStack_7c [4];
  undefined4 uStack_78;
  undefined4 uStack_74;
  undefined4 uStack_70;
  undefined4 uStack_6c;
  undefined4 auStack_68 [2];
  undefined4 uStack_60;
  undefined4 uStack_5c;
  undefined4 uStack_58;
  undefined4 uStack_54;
  undefined4 uStack_50;
  undefined4 uStack_4c;
  int iStack_40;
  int iStack_3c;
  int iStack_30;
  
  iStack_40 = param_1;
code_r0x1000a33a:
  do {
    while( true ) {
      uVar10 = (**(code **)(iStack_40 + 0xc))(iStack_40,PTR_DAT_10006024,0x10,1);
      if ((8 < (int)uVar10) &&
         (iVar11 = func_0x1001b56c(PTR_DAT_10006024,PTR_DAT_10006028,9), iVar11 == 0)) {
        if (9 < (int)uVar10) {
          (**(code **)(iStack_40 + 0x14))(iStack_40,PTR_DAT_1000602c,uVar10 - 9);
        }
        return 0;
      }
      if ((bool)in_b7) {
        return 0;
      }
      if ((int)uVar10 < 0x10) {
        (**(code **)(iStack_40 + 0x14))(iStack_40,PTR_DAT_10006024,uVar10);
        return 0xfffffffe;
      }
      if (*(short *)PTR_DAT_10006024 != 0xac) {
        (**(code **)(iStack_40 + 0x14))(iStack_40,PTR_DAT_10006024,uVar10);
        return 0xfffffffe;
      }
      FUN_1001b4c8(PTR_DAT_10006030,0,0x10);
      puVar4 = PTR_DAT_10006030;
      puVar15 = PTR_DAT_10006024;
      *(undefined2 *)PTR_DAT_10006030 = 0xac;
      *(undefined2 *)(puVar4 + 4) = 1;
      puVar9 = PTR_DAT_1000606c;
      puVar8 = PTR_DAT_1000603c;
      puVar7 = PTR_s_20050309_10006038;
      puVar6 = PTR_DAT_10006034;
      puVar5 = PTR_DAT_10006030;
      puVar4 = PTR_DAT_10006024;
      uVar2 = *(ushort *)(puVar15 + 2);
      uVar19 = (uint)uVar2;
      if (uVar19 != 0xb) break;
      iVar17 = *(int *)PTR_DAT_10005cfc - *(int *)PTR_DAT_10005cf8;
      iVar13 = FUN_100131b8(iVar17 + 4,2);
      puVar4 = PTR_DAT_10005cfc;
      puVar15 = PTR_DAT_10005cf0;
      iVar11 = DAT_1000605c;
      if (iVar13 != 0) {
        FUN_1001b38c(iVar13,*(int *)PTR_DAT_10005cf0,
                     *(int *)PTR_DAT_10005cfc - *(int *)PTR_DAT_10005cf0);
        FUN_1001b38c(iVar13 + (*(int *)puVar4 - *(int *)puVar15),*(int *)PTR_DAT_10005cf8,
                     *(int *)puVar15 - *(int *)PTR_DAT_10005cf8);
        iVar11 = 0;
      }
      puVar15 = PTR_DAT_10006030;
      if (iVar11 == 0) {
        puVar1 = (ushort *)(PTR_DAT_10006030 + 10);
        *(uint *)(PTR_DAT_10006030 + 4) =
             *(uint *)(PTR_DAT_10006030 + 4) & DAT_10005d04 | iVar17 + 4U >> 0x10;
        *(uint *)(puVar15 + 8) = (uint)*puVar1 | (iVar17 + 4U) * 0x10000;
        uStack_6c = FUN_100116b0(iVar13,iVar17);
        FUN_1001b38c(iVar13 + iVar17,&uStack_6c,4);
      }
      else {
        *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
      }
      puVar15 = PTR_DAT_10006030;
      *(undefined2 *)(PTR_DAT_10006030 + 2) = 0xb;
      func_0x1000ae00(iStack_40);
      if (iVar11 == 0) {
        uVar18 = *(undefined2 *)(puVar15 + 6);
code_r0x1000ab98:
        (**(code **)(iStack_40 + 0x10))
                  (iStack_40,iVar13,CONCAT22(uVar18,*(undefined2 *)(puVar15 + 8)));
      }
      else if (iVar13 != 0) {
        FUN_10013408(iVar13);
      }
    }
    if (0xb < uVar19) {
      if (uVar19 == _UNK_1000607c) {
        uVar19 = *(uint *)(PTR_DAT_10006024 + 4);
        FUN_1001693c(auStack_a0,PTR_DAT_1000603c);
        FUN_1001b38c(puVar8,PTR_s_PENDING_10006040,8);
        func_0x10011e6c();
        FUN_10012644(0);
        func_0x10013478();
        iVar11 = FUN_100131b8(uVar19,2);
        uVar10 = _UNK_10006044;
        if (iVar11 == 0) {
          iVar11 = FUN_100131b8(_UNK_10006044,2);
          uVar12 = 0;
          if ((iVar11 != 0) && (uVar19 != 0)) {
            do {
              uVar22 = uVar10;
              if (uVar19 - uVar12 <= uVar10) {
                uVar22 = uVar19 - uVar12;
              }
              iStack_30 = iVar11;
              iVar13 = (**(code **)(iStack_40 + 0xc))(iStack_40,iVar11,uVar22,0);
              iVar11 = iStack_30;
            } while ((0 < iVar13) && (uVar12 = uVar12 + iVar13, uVar12 < uVar19));
          }
        }
        else {
          uStack_90 = 0x2c;
          uStack_88 = 10;
          uStack_8c = DAT_10006048;
          iStack_30 = iVar11;
          FUN_10013658(10,&uStack_90);
          uVar10 = 0;
          if (uVar19 == 0) {
code_r0x1000a571:
            FUN_100116b0(iStack_30,uVar19 - 4);
                    /* WARNING: Bad instruction - Truncating control flow here */
            halt_baddata();
          }
          while (iVar13 = (**(code **)(iStack_40 + 0xc))
                                    (iStack_40,iStack_30 + uVar10,uVar19 - uVar10,0),
                iVar11 = iStack_30, 0 < iVar13) {
            uVar10 = uVar10 + iVar13;
            if (uVar19 <= uVar10) goto code_r0x1000a571;
          }
        }
        FUN_10013408(iVar11);
        FUN_1001693c(PTR_DAT_1000603c,auStack_a0);
        func_0x10011e6c();
        FUN_100126b0(0);
        goto code_r0x1000a33a;
      }
      if ((int)_UNK_1000607c < (int)uVar19) {
        if (uVar19 == _UNK_10006064) {
          iVar13 = *(int *)(PTR_DAT_10006024 + 4);
          iVar11 = FUN_100131b8(iVar13,2);
          if (iVar11 == 0) {
            iVar17 = 0;
          }
          else {
            iVar14 = (**(code **)(iStack_40 + 0xc))(iStack_40,iVar11,iVar13,0);
            iVar17 = 0;
            if (-1 < iVar14) {
              iVar17 = iVar14;
            }
          }
          iVar14 = 0;
          if (iVar17 != iVar13) {
            iVar14 = DAT_1000605c;
          }
          if ((iVar14 != 0) || (iVar13 = func_0x1000ad7c(iVar11,iVar13,1), iVar13 != 0)) {
            *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
          }
          *(short *)(PTR_DAT_10006030 + 2) = (short)_UNK_10006064;
code_r0x1000ad0c:
          func_0x1000ae00(iStack_40);
          FUN_10013408(iVar11);
          goto code_r0x1000a33a;
        }
        if ((int)uVar19 <= (int)_UNK_10006064) {
          if (uVar19 == _UNK_10006080) {
            (**(code **)(*(int *)PTR_DAT_10006068 + 4))();
          }
          goto code_r0x1000a33a;
        }
        if (uVar19 != _UNK_10006060) goto code_r0x1000a33a;
        uStack_80 = 0xffffffff;
        uVar10 = *(uint *)(PTR_DAT_10006024 + 8);
        sVar3 = *(short *)(PTR_DAT_10006024 + 6);
        iStack_3c = FUN_100131b8(uVar10,2);
        if (iStack_3c == 0) {
          uVar19 = 0;
        }
        else {
          uVar12 = (**(code **)(iStack_40 + 0xc))(iStack_40,iStack_3c,uVar10,0);
          uVar19 = 0;
          if (-1 < (int)uVar12) {
            uVar19 = uVar12;
          }
        }
        if (uVar19 != uVar10) {
          if (iStack_3c != 0) {
            FUN_10013408(iStack_3c);
          }
          goto code_r0x1000a33a;
        }
        func_0x100111ec();
        if (sVar3 < 0x101) {
          puVar16 = (undefined4 *)FUN_100131b8(0x100,1);
          uVar21 = 0;
          uVar23 = 2;
        }
        else {
          puVar16 = (undefined4 *)FUN_100131b8(0x100,1);
          uVar21 = 0x1fc;
          uVar23 = 4;
        }
        iVar11 = FUN_100117e8(&uStack_80,uVar21,uVar23,0);
        if (iVar11 == 0) {
          FUN_100117e8(iStack_3c,sVar3,uVar10 & 0xffff,0);
        }
        if (sVar3 < 0x101) {
          FUN_100117e8(puVar16,2,0xfe,1);
          auStack_7c = (undefined1  [4])FUN_100116b0(puVar16,0xfe);
          puVar20 = (undefined4 *)((int)auStack_7c + 2);
          uVar21 = 0;
          uVar23 = 2;
        }
        else {
          FUN_100117e8(puVar16,0x100,0xfc,1);
          auStack_7c = (undefined1  [4])FUN_100116b0(puVar16,0xfc);
          puVar20 = (undefined4 *)auStack_7c;
          uVar21 = 0x1fc;
          uVar23 = 4;
        }
        iVar11 = FUN_100117e8(puVar20,uVar21,uVar23,0);
        func_0x10011204();
        if (iVar11 != 0) {
          *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
        }
        *(short *)(PTR_DAT_10006030 + 2) = (short)_UNK_10006060;
        func_0x1000ae00(iStack_40);
        if (iStack_3c != 0) {
          FUN_10013408(iStack_3c);
        }
      }
      else {
        if (uVar19 == 0xd) {
          *(ushort *)(PTR_DAT_10006030 + 2) = uVar2;
          *(undefined4 *)PTR_DAT_10005d00 = *(undefined4 *)(puVar4 + 4);
          func_0x1000ae00(iStack_40);
          goto code_r0x1000a33a;
        }
        if (0xc < uVar19) {
          if (uVar19 == 0xf) {
            iVar13 = *(int *)(PTR_DAT_10006024 + 0xc);
            iVar11 = FUN_100131b8(iVar13,2);
            if (iVar11 == 0) {
              iVar17 = 0;
            }
            else {
              iVar14 = (**(code **)(iStack_40 + 0xc))(iStack_40,iVar11,iVar13,0);
              iVar17 = 0;
              if (-1 < iVar14) {
                iVar17 = iVar14;
              }
            }
            iVar14 = 0;
            if (iVar17 != iVar13) {
              iVar14 = DAT_1000605c;
            }
            if ((iVar14 != 0) ||
               (iVar13 = func_0x1000adec(iVar11,iVar13,*(undefined4 *)(PTR_DAT_10006024 + 8),
                                         *(undefined2 *)(PTR_DAT_10006024 + 4),
                                         *(undefined2 *)(PTR_DAT_10006024 + 6)), iVar13 != 0)) {
              *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
            }
            *(undefined2 *)(PTR_DAT_10006030 + 2) = 0xf;
            goto code_r0x1000ad0c;
          }
          goto code_r0x1000a33a;
        }
        puVar16 = (undefined4 *)0x0;
        uVar19 = *(uint *)(PTR_DAT_10006024 + 4);
        iVar11 = DAT_1000605c;
        if (uVar19 == 0x20) {
          puVar16 = (undefined4 *)FUN_100131b8(0x20,2);
          if (puVar16 == (undefined4 *)0x0) {
            uVar10 = 0;
            iVar11 = DAT_1000605c;
          }
          else {
            uVar10 = (**(code **)(iStack_40 + 0xc))(iStack_40,puVar16,0x20,0);
            uVar10 = uVar10 & (int)(((int)uVar10 >> 0x1f) - uVar10) >> 0x1f;
            iVar11 = 0;
          }
        }
        iVar13 = DAT_1000605c;
        if (uVar10 == uVar19) {
          auStack_68[0] = FUN_100116b0(puVar16,uVar19 - 4);
          iVar17 = func_0x1001b320(auStack_68,(int)puVar16 + (uVar19 - 4),4);
          iVar13 = iVar11;
          if (iVar17 != 0) {
            iVar13 = DAT_1000605c;
          }
        }
        if (iVar13 == 0) {
          uStack_60 = *puVar16;
          uStack_5c = puVar16[1];
          uStack_58 = puVar16[2];
          uStack_54 = puVar16[3];
          uStack_50 = puVar16[4];
          uStack_4c = puVar16[5];
          (**(code **)(*(int *)PTR_DAT_10006068 + 0xc))(&uStack_60,puVar16[6]);
        }
        else {
          *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
        }
        uVar18 = 0xc;
code_r0x1000ac69:
        *(undefined2 *)(PTR_DAT_10006030 + 2) = uVar18;
        func_0x1000ae00(iStack_40);
      }
      if (puVar16 != (undefined4 *)0x0) {
        FUN_10013408(puVar16);
      }
      goto code_r0x1000a33a;
    }
    if (uVar19 == 6) {
      *(undefined2 *)(PTR_DAT_10006030 + 6) = **(undefined2 **)PTR_DAT_1000606c;
      iVar13 = FUN_100131b8(*(undefined2 *)(puVar5 + 6),2);
      iVar11 = DAT_1000605c;
      if (iVar13 != 0) {
        FUN_1001b38c(iVar13,*(undefined4 *)puVar9,*(undefined2 *)(PTR_DAT_10006030 + 6));
        iVar11 = 0;
      }
      if (iVar11 != 0) {
        *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
      }
      puVar15 = PTR_DAT_10006030;
      *(undefined2 *)(PTR_DAT_10006030 + 2) = 6;
      func_0x1000ae00(iStack_40);
      if (iVar11 != 0) goto code_r0x1000aa10;
      (**(code **)(iStack_40 + 0x10))(iStack_40,iVar13,*(undefined2 *)(puVar15 + 6));
    }
    else if (uVar19 < 7) {
      if (uVar19 == 2) {
        *(ushort *)(PTR_DAT_10006030 + 2) = uVar2;
        puVar5[6] = 0;
        func_0x1000ae00(iStack_40);
      }
      else if (uVar19 < 3) {
        if (uVar19 == 1) {
          *(ushort *)(PTR_DAT_10006030 + 2) = uVar2;
          FUN_1001b38c(puVar6,puVar7,8);
          *(undefined2 *)(puVar5 + 0xe) = *(undefined2 *)PTR_DAT_10005fa8;
          func_0x1000ae00(iStack_40);
        }
      }
      else if (uVar19 == 3) {
        iVar13 = 0;
        iVar11 = DAT_1000605c;
        if (((*(uint *)(PTR_DAT_10006024 + 4) <= DAT_10005f20) &&
            (*(uint *)(PTR_DAT_10006024 + 4) + *(int *)(PTR_DAT_10006024 + 8) <= DAT_10005f20)) &&
           (iVar13 = FUN_100131b8(*(int *)(PTR_DAT_10006024 + 8) + 4,2), iVar11 = DAT_1000605c,
           iVar13 != 0)) {
          iVar11 = FUN_100117e8(iVar13,*(undefined2 *)(PTR_DAT_10006024 + 6),
                                *(undefined2 *)(PTR_DAT_10006024 + 10),1);
        }
        puVar4 = PTR_DAT_10006030;
        puVar15 = PTR_DAT_10006024;
        if (iVar11 == 0) {
          puVar1 = (ushort *)(PTR_DAT_10006030 + 10);
          uVar2 = *(ushort *)(PTR_DAT_10006024 + 10);
          *(uint *)(PTR_DAT_10006030 + 4) =
               *(uint *)(PTR_DAT_10006030 + 4) & DAT_10005d04 | uVar2 + 4 >> 0x10;
          *(uint *)(puVar4 + 8) = (uint)*puVar1 | (uVar2 + 4) * 0x10000;
          uStack_78 = FUN_100116b0(iVar13);
          FUN_1001b38c(iVar13 + (uint)*(ushort *)(puVar15 + 10),&uStack_78,4);
        }
        else {
          *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
        }
        *(undefined2 *)(PTR_DAT_10006030 + 2) = 3;
        func_0x1000ae00(iStack_40);
        if (iVar11 != 0) goto code_r0x1000aa10;
        (**(code **)(iStack_40 + 0x10))(iStack_40,iVar13,*(int *)(PTR_DAT_10006024 + 8) + 4);
      }
    }
    else {
      if (uVar19 == 9) {
        iVar13 = 0;
        iVar11 = DAT_1000605c;
        if (((*(uint *)(PTR_DAT_10006024 + 4) <= _UNK_10006074) &&
            (*(uint *)(PTR_DAT_10006024 + 8) <= DAT_10005dc8)) &&
           (iVar13 = FUN_100131b8(*(uint *)(PTR_DAT_10006024 + 8) + 4,2), iVar11 = DAT_1000605c,
           iVar13 != 0)) {
          FUN_1001b38c(iVar13,*(undefined4 *)(PTR_DAT_10006024 + 4),
                       *(undefined4 *)(PTR_DAT_10006024 + 8));
          iVar11 = 0;
        }
        puVar4 = PTR_DAT_10006030;
        puVar15 = PTR_DAT_10006024;
        if (iVar11 == 0) {
          puVar1 = (ushort *)(PTR_DAT_10006030 + 10);
          iVar17 = *(int *)(PTR_DAT_10006024 + 8);
          *(uint *)(PTR_DAT_10006030 + 4) =
               *(uint *)(PTR_DAT_10006030 + 4) & DAT_10005d04 | iVar17 + 4U >> 0x10;
          *(uint *)(puVar4 + 8) = (uint)*puVar1 | (iVar17 + 4U) * 0x10000;
          uStack_74 = FUN_100116b0(iVar13);
          FUN_1001b38c(iVar13 + (uint)*(ushort *)(puVar15 + 10),&uStack_74,4);
        }
        else {
          *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
        }
        puVar15 = PTR_DAT_10006030;
        *(undefined2 *)(PTR_DAT_10006030 + 2) = 9;
        func_0x1000ae00(iStack_40);
        if (iVar11 == 0) {
          uVar18 = *(undefined2 *)(puVar15 + 6);
          goto code_r0x1000ab98;
        }
        goto code_r0x1000aa10;
      }
      if (9 < uVar19) {
        puVar16 = (undefined4 *)0x0;
        iStack_3c = 0;
        iVar11 = *(int *)(PTR_DAT_10006024 + 4);
        uVar19 = *(uint *)(PTR_DAT_10006024 + 8);
        if ((_UNK_10006078 < (uint)(iVar11 + DAT_10005ccc)) || (DAT_10005dc8 < uVar19)) {
          iStack_3c = DAT_1000605c;
        }
        else {
          puVar16 = (undefined4 *)FUN_100131b8(uVar19,2);
          if (puVar16 == (undefined4 *)0x0) {
            uVar10 = 0;
            iStack_3c = DAT_1000605c;
          }
          else {
            uVar10 = (**(code **)(iStack_40 + 0xc))(iStack_40,puVar16,uVar19,0);
            uVar10 = uVar10 & (int)(((int)uVar10 >> 0x1f) - uVar10) >> 0x1f;
          }
        }
        if (uVar10 == uVar19) {
          uStack_70 = FUN_100116b0(puVar16,uVar19 - 4);
          iVar13 = func_0x1001b320(&uStack_70,(int)puVar16 + (uVar19 - 4),4);
          if (iVar13 != 0) {
            iStack_3c = DAT_1000605c;
          }
          if (iStack_3c == 0) {
            FUN_1001b38c(iVar11,puVar16,uVar19 - 4);
            goto code_r0x1000aacb;
          }
code_r0x1000aad0:
          *(undefined2 *)(PTR_DAT_10006030 + 4) = 0;
        }
        else {
          iStack_3c = DAT_1000605c;
code_r0x1000aacb:
          if (iStack_3c != 0) goto code_r0x1000aad0;
        }
        uVar18 = 10;
        goto code_r0x1000ac69;
      }
      if (uVar19 == 8) {
        iVar13 = FUN_100131b8(0x43,2);
        iVar11 = DAT_1000605c;
        if (iVar13 != 0) {
          FUN_1001b38c(iVar13,PTR_s_TIME_Wed_Mar_09_12_27_39_2005_BO_10006070,0x42);
          *(undefined1 *)(iVar13 + 0x42) = 0;
          iVar11 = 0;
        }
        puVar15 = PTR_DAT_10006030;
        *(undefined2 *)(PTR_DAT_10006030 + 2) = 8;
        if (iVar11 == 0) {
          *(undefined2 *)(PTR_DAT_10006030 + 6) = 0x42;
        }
        else {
          *(undefined2 *)(puVar15 + 4) = 0;
          *(undefined2 *)(puVar15 + 6) = 0;
        }
        func_0x1000ae00(iStack_40);
        if (iVar11 == 0) {
          (**(code **)(iStack_40 + 0x10))(iStack_40,iVar13,0x42);
        }
        else {
code_r0x1000aa10:
          if (iVar13 != 0) {
            FUN_10013408(iVar13);
          }
        }
      }
    }
  } while( true );
}


