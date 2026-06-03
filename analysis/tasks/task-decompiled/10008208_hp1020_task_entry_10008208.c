/* Function: 10008208 hp1020_task_entry_10008208 */


void hp1020_task_entry_10008208(void)

{
  byte bVar1;
  char cVar2;
  undefined *puVar3;
  undefined4 uVar4;
  int *piVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint *puVar10;
  int iVar11;
  uint uVar12;
  byte bVar14;
  uint uVar13;
  byte *pbVar15;
  uint uStack_28;
  uint uStack_24;
  
  puVar10 = DAT_10005dec;
  memw();
  uVar7 = *DAT_10005de4;
  memw();
  uVar12 = *DAT_10005de8;
  if ((uVar7 & 8) != 0) {
    memw();
    *DAT_10005de4 = 8;
    memw();
    if ((*puVar10 & 0x10) == 0) {
      iVar11 = FUN_10011178(0x15);
      *PTR_DAT_10005df0 = 0;
      if (iVar11 != 2) {
        memw();
        memw();
        *DAT_10005df4 = *DAT_10005df4 & 0xfffffffc;
      }
    }
    else {
      bVar1 = *PTR_DAT_10005df0;
      bVar14 = bVar1 + 1;
      *PTR_DAT_10005df0 = bVar14;
      puVar3 = PTR_DAT_10005df8;
      if (bVar1 < 2) {
        if (1 < bVar14) {
          uVar13 = *(int *)PTR_DAT_10005df8 + (uint)*(ushort *)PTR_DAT_10005dfc * 1000000;
          uVar6 = FUN_1001bb5c();
          uVar8 = *(uint *)puVar3;
          if (((uVar8 < uVar13) && ((uVar13 < uVar6 || (uVar6 < uVar8)))) ||
             ((uVar13 < uVar8 && ((uVar13 < uVar6 && (uVar6 < uVar8)))))) {
            *PTR_DAT_10005df0 = 1;
          }
        }
        puVar3 = PTR_DAT_10005df8;
        uVar4 = FUN_1001bb5c();
        *(undefined4 *)puVar3 = uVar4;
      }
      else {
        uVar13 = *(int *)PTR_DAT_10005df8 + (uint)*(ushort *)PTR_DAT_10005dfc * 1000000;
        uVar6 = FUN_1001bb5c();
        uVar8 = *(uint *)puVar3;
        if (((uVar8 < uVar13) && (uVar6 < uVar13)) ||
           ((uVar13 < uVar8 && ((uVar6 < uVar13 || (uVar8 < uVar6)))))) {
          iVar11 = FUN_10011178(0x15);
          if (iVar11 - 1U < 2) {
            memw();
            memw();
            memw();
            *DAT_10005df4 = *DAT_10005df4 & 0xfffffffc | 1 | *DAT_10005df4 & 3;
          }
          *PTR_DAT_10005df0 = 0;
        }
      }
    }
  }
  if ((uVar7 & 1) != 0) {
    memw();
    *DAT_10005de4 = 1;
  }
  if ((uVar7 & 2) != 0) {
    memw();
    *DAT_10005de4 = 2;
  }
  if ((uVar7 & 0x10) != 0) {
    memw();
    *DAT_10005de4 = 0x10;
  }
  if ((uVar7 & 0x20) != 0) {
    memw();
    *DAT_10005de4 = 0x20;
  }
  if ((uVar7 & 0x40) != 0) {
    memw();
    *DAT_10005de4 = 0x40;
  }
  uVar7 = 0;
  uVar6 = 0;
  memw();
  uVar13 = *DAT_10005e00;
  memw();
  *DAT_10005de8 = uVar12;
  do {
    uVar8 = 0;
    uStack_28 = (uVar13 ^ 0xffffffff) >> (uVar6 & 0x1f) & 0xffff;
    uStack_24 = uVar12 >> (uVar6 & 0x1f) & 0xffff;
    do {
      if (uStack_28 == 0) break;
      if ((uStack_24 & 1) != 0) {
        iVar11 = DAT_10005e08;
        if (uVar7 == 0) {
          iVar11 = DAT_10005e04;
        }
        puVar10 = (uint *)(uVar8 * 0x20 + iVar11);
        memw();
        uVar9 = *puVar10;
        if ((uVar9 & 0x200) != 0) {
          memw();
          *puVar10 = 0x200;
        }
        if ((uVar9 & 0x80) != 0) {
          memw();
          *puVar10 = 0x80;
        }
        if ((uVar9 & 0x40) != 0) {
          memw();
          *puVar10 = 0x40;
          if ((1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)) == 2) && (*PTR_DAT_10005e0c == '\0')) {
            for (piVar5 = (int *)FUN_100130bc(PTR_DAT_10005e10); piVar5 != (int *)0x0;
                piVar5 = (int *)*piVar5) {
              if (*(int *)(piVar5[3] + 8) != 0) {
                FUN_1000899c(piVar5[3]);
                *PTR_DAT_10005e0c = 1;
                break;
              }
            }
          }
        }
        if ((uVar9 & 0x30) != 0) {
          memw();
          *puVar10 = uVar9 & 0x30;
        }
        if ((uVar9 & 0x400) != 0) {
          memw();
          *puVar10 = 0x400;
          puVar3 = PTR_DAT_10005e10;
          iVar11 = 1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f));
          if (iVar11 == 2) {
            if (*PTR_DAT_10005e0c != '\0') {
              *PTR_DAT_10005e0c = 0;
              piVar5 = (int *)FUN_100130bc(puVar3);
              puVar3 = PTR_DAT_10005e14;
              for (; piVar5 != (int *)0x0; piVar5 = (int *)*piVar5) {
                iVar11 = piVar5[3];
                if ((*(int *)(iVar11 + 8) == 0) && (*(int *)(iVar11 + 0xc) == 0)) {
                  *(undefined4 *)(iVar11 + 0xc) = 1;
                  puVar10 = DAT_10005e00;
                  if (*piVar5 == 0) {
                    memw();
                    uVar9 = *DAT_10005e00;
                    *(undefined4 *)puVar3 = 0;
                    memw();
                    *puVar10 = uVar9 | 2;
                  }
                  break;
                }
              }
            }
          }
          else {
            FUN_10017dac(PTR_DAT_10005e18,iVar11,0);
          }
        }
        if (uVar7 == 1) {
          FUN_10007c5c(*(undefined4 *)PTR_DAT_10005e1c);
          if ((uVar8 == 1) && (*PTR_DAT_10005e20 != '\0')) {
            memw();
            cVar2 = *PTR_DAT_10005e28;
            memw();
            *(uint *)(DAT_10005e24 + 0x20) = *(uint *)(DAT_10005e24 + 0x20) | 0x80;
            if (cVar2 == '\0') {
              pbVar15 = *(byte **)PTR_DAT_10005e2c;
              if ((((uint)pbVar15[3] |
                   (uint)pbVar15[2] << 8 | (uint)pbVar15[1] << 0x10 | (uint)*pbVar15 << 0x18) &
                  DAT_10005e30) == DAT_10005e34) {
                uVar9 = (uint)*(ushort *)(pbVar15 + 2);
                if (*(int *)PTR_DAT_10005e38 == 0) {
                  *(undefined4 *)PTR_DAT_10005e3c = 0;
LAB_1000855d:
                  FUN_1001b38c(*(int *)PTR_DAT_10005e44 +
                               *(int *)PTR_DAT_10005e38 + *(int *)PTR_DAT_10005e3c,
                               *(int *)PTR_DAT_10005e44 + *(int *)PTR_DAT_10005e40,uVar9);
                }
                else if (*(int *)PTR_DAT_10005e3c + *(int *)PTR_DAT_10005e38 !=
                         *(int *)PTR_DAT_10005e40) goto LAB_1000855d;
                puVar3 = PTR_DAT_10005e48;
                *(uint *)PTR_DAT_10005e38 = *(int *)PTR_DAT_10005e38 + uVar9;
                *puVar3 = 0;
                if (*(int *)PTR_DAT_10005e4c - uVar9 < *(uint *)PTR_DAT_10005e50) {
                  *(undefined4 *)PTR_DAT_10005e54 = 0;
                }
                else if (*(int *)PTR_DAT_10005e54 != 0) {
                  *(uint *)PTR_DAT_10005e54 = *(int *)PTR_DAT_10005e54 + uVar9;
                }
              }
            }
            else {
              uVar9 = (uint)(byte)*PTR_DAT_10005e58;
              do {
                pbVar15 = (byte *)(uVar9 * 0x10 + *(int *)PTR_DAT_10005e2c);
                if ((((uint)pbVar15[3] |
                     (uint)pbVar15[2] << 8 | (uint)pbVar15[1] << 0x10 | (uint)*pbVar15 << 0x18) &
                    DAT_10005e30) == DAT_10005e34) {
                  uVar9 = 0;
                  *(uint *)PTR_DAT_10005e4c =
                       *(int *)PTR_DAT_10005e4c - (uint)*(ushort *)(pbVar15 + 2);
                  *(uint *)PTR_DAT_10005e5c =
                       *(int *)PTR_DAT_10005e5c + (uint)*(ushort *)(pbVar15 + 2);
                  break;
                }
                uVar9 = uVar9 - 1;
              } while (uVar9 != 0xffffffff);
              if (*(int *)PTR_DAT_10005e54 != 0) {
                *(uint *)PTR_DAT_10005e54 =
                     *(int *)PTR_DAT_10005e54 +
                     (uint)*(ushort *)(uVar9 * 0x10 + *(int *)PTR_DAT_10005e2c + 2);
              }
              if (*(int *)PTR_DAT_10005e4c < *(int *)PTR_DAT_10005e50) {
                *(undefined4 *)PTR_DAT_10005e54 = 0;
              }
              *PTR_DAT_10005e48 = 1;
            }
            if (*(int *)PTR_DAT_10005e38 == 0) {
              *(undefined4 *)PTR_DAT_10005e3c = 0;
            }
            puVar3 = PTR_DAT_10005e40;
            uVar9 = *(int *)PTR_DAT_10005e3c + *(int *)PTR_DAT_10005e38;
            *(uint *)PTR_DAT_10005e40 = uVar9;
            if ((uVar9 & 0xf) != 0) {
              *(uint *)puVar3 = (uVar9 & 0xfffffff0) + 0x10;
            }
            FUN_100086f4(*(undefined4 *)PTR_DAT_10005e40);
          }
          FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0);
        }
      }
      uVar8 = uVar8 + 1;
      uStack_28 = uStack_28 >> 1;
      uStack_24 = uStack_24 >> 1;
    } while (uVar8 < 0x10);
    uVar6 = uVar6 + 0x10;
    uVar7 = uVar7 + 1;
    if (1 < uVar7) {
      FUN_100171e0(4);
      return;
    }
  } while( true );
}


