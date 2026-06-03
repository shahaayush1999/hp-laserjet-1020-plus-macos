/* Function: 1000f574 FUN_1000f574 */


void FUN_1000f574(int *param_1)

{
  char cVar1;
  bool bVar2;
  bool bVar3;
  bool bVar4;
  bool bVar5;
  bool bVar6;
  undefined *puVar7;
  int iVar8;
  int iVar9;
  undefined4 uVar10;
  bool bVar11;
  undefined4 uVar12;
  undefined4 uVar13;
  undefined4 uVar14;
  undefined4 uVar15;
  
  puVar7 = PTR_DAT_10006338;
  bVar2 = false;
  bVar3 = false;
  bVar4 = false;
  if ((*PTR_DAT_10006338 != '\0') && (bVar3 = true, PTR_DAT_10006338[1] == '\0')) {
    bVar3 = false;
  }
  if (bVar3) {
    bVar2 = PTR_DAT_10006338[2] != '\0';
  }
  if (*PTR_DAT_10006338 != '\0') {
    bVar4 = *(int *)(PTR_DAT_10006338 + 0xc) == 3;
  }
  iVar8 = FUN_100130bc(PTR_DAT_10006328);
  bVar3 = iVar8 != 0;
  iVar8 = FUN_1000fcb0(param_1);
  bVar11 = false;
  if (iVar8 != 0) {
    if (iVar8 != 8) {
      if (iVar8 == 9) {
        *(undefined4 *)(puVar7 + 0xc) = 0;
        FUN_10010158();
        bVar11 = false;
        goto LAB_1000f5eb;
      }
      *(undefined4 *)(puVar7 + 0xc) = 2;
      FUN_10010170();
    }
    bVar11 = true;
  }
LAB_1000f5eb:
  if (!bVar11) {
    bVar11 = false;
    do {
      iVar8 = FUN_100130bc(PTR_DAT_10006324);
      bVar5 = bVar2;
      if (iVar8 == 0) goto switchD_1000f611_caseD_1;
      uVar10 = *(undefined4 *)(iVar8 + 0xc);
      switch(*(undefined4 *)(iVar8 + 4)) {
      case 0:
        bVar6 = false;
        if (*(int *)(PTR_DAT_10006338 + 0xc) == 2) {
          *(undefined4 *)(iVar8 + 4) = 7;
        }
        else if ((!bVar3) || (*(int *)(PTR_DAT_1000633c + 0xc) != 1)) {
          if ((*(ushort *)(PTR_DAT_10006338 + 0x12) == DAT_10006364) &&
             (bVar5 = true, *(int *)(PTR_DAT_10006338 + 4) != 0)) {
            bVar5 = bVar2;
          }
          if (bVar5) {
            if (bVar4) {
LAB_1000f6a0:
              bVar6 = true;
            }
            else {
              iVar9 = FUN_1000f84c(uVar10,0);
              if (iVar9 != 0) {
                iVar9 = FUN_100130bc(PTR_DAT_10006328);
                if (iVar9 == 0) {
                  *(undefined4 *)(PTR_DAT_10006338 + 0xc) = 2;
                  FUN_10010170();
                }
                else {
                  *(undefined4 *)(PTR_DAT_10006338 + 0xc) = 1;
                }
                *(undefined4 *)(iVar8 + 4) = 7;
                goto LAB_1000f6a8;
              }
              *(undefined4 *)(PTR_DAT_10006338 + 0xc) = 0;
              bVar6 = true;
            }
          }
          else {
            if (bVar4) goto LAB_1000f6a0;
LAB_1000f6a8:
            bVar11 = true;
          }
          if (bVar6) {
            *(undefined4 *)(iVar8 + 4) = 1;
            FUN_10010218(0,0xd,0,0,uVar10);
            bVar11 = true;
          }
          goto LAB_1000f80e;
        }
        break;
      case 2:
        if (((bVar2) || (bVar4)) && (*(int *)(iVar8 + 8) == 1)) {
          *(undefined4 *)(iVar8 + 4) = 3;
          FUN_10010218(8,0xb,0,0,uVar10);
        }
        break;
      case 4:
        if (((!bVar2) && (!bVar4)) || (*(int *)(iVar8 + 8) != 1)) break;
        iVar8 = FUN_10013050(PTR_DAT_10006324);
        FUN_10013000(PTR_DAT_10006328,iVar8);
        *(undefined4 *)(iVar8 + 4) = 5;
        FUN_10010218(0,0xb,0,0,uVar10);
        cVar1 = PTR_DAT_10006338[2];
        PTR_DAT_10006338[2] = cVar1 + -1;
        if ((char)(cVar1 + -1) == '\0') {
          bVar11 = true;
        }
        bVar3 = true;
        goto LAB_1000f80e;
      case 7:
        iVar9 = FUN_100130bc(PTR_DAT_10006328);
        if (((*param_1 == 0x11) && (*(int *)(PTR_DAT_10006338 + 0xc) == 1)) && (iVar9 == 0)) {
          *(undefined4 *)(PTR_DAT_10006338 + 0xc) = 2;
LAB_1000f765:
          FUN_10010170();
        }
        else {
          bVar2 = false;
          uVar12 = 4;
          if (*param_1 == 0x32) {
            FUN_10010318(*(undefined4 *)(PTR_DAT_10006344 + 0x10),4);
            if (param_1[1] == 1) {
              FUN_100100a8();
              uVar12 = 1;
            }
            else {
              uVar12 = 2;
            }
LAB_1000f7a4:
            bVar2 = true;
          }
          else if (*param_1 == 0x34) {
            uVar12 = 3;
            goto LAB_1000f7a4;
          }
          if (bVar2) {
            iVar9 = FUN_1000f84c(uVar10,uVar12);
            uVar12 = DAT_1000604c;
            if (iVar9 == 0) {
              *(undefined4 *)(PTR_DAT_10006338 + 0xc) = 0;
              *(undefined4 *)(iVar8 + 4) = 1;
              FUN_10010218(10,0x2c,uVar12,1,0);
              uVar13 = 0xd;
              uVar12 = 0;
              uVar15 = 0;
              uVar14 = 0;
            }
            else {
              if (iVar9 != 6) goto LAB_1000f765;
              FUN_10010218(10,0xf,2,0,0);
              uVar12 = 10;
              uVar13 = 0x2c;
              uVar15 = 1;
              uVar10 = 0;
              uVar14 = DAT_1000604c;
            }
            bVar11 = true;
            FUN_10010218(uVar12,uVar13,uVar14,uVar15,uVar10);
            FUN_10010158();
            goto LAB_1000f80e;
          }
        }
      }
switchD_1000f611_caseD_1:
      bVar11 = true;
LAB_1000f80e:
      bVar2 = bVar5;
    } while (!bVar11);
  }
  return;
}


