/* Function: 1000e414 hp1020_job_mgr_thread_candidate */


void hp1020_job_mgr_thread_candidate(void)

{
  short sVar1;
  bool bVar2;
  int *piVar3;
  undefined *puVar4;
  undefined *puVar5;
  undefined *puVar6;
  undefined *puVar7;
  int iVar8;
  int iVar9;
  undefined1 uVar10;
  char cVar11;
  int *piVar12;
  int *piVar13;
  undefined4 uVar14;
  int iVar15;
  uint uVar16;
  undefined4 uStack_90;
  uint uStack_8c;
  undefined4 uStack_88;
  int iStack_84;
  undefined4 uStack_80;
  uint uStack_7c;
  undefined4 uStack_78;
  undefined4 uStack_74;
  undefined4 auStack_70 [8];
  undefined4 uStack_50;
  int *piStack_4c;
  int iStack_40;
  undefined4 uStack_3c;
  int iStack_38;
  char cStack_21;
  
  uVar16 = 0;
  FUN_1001214c();
switchD_1000e461_caseD_4:
  while( true ) {
    uVar16 = uVar16 & 0xffffcfff;
    iVar8 = FUN_1001809c(PTR_DAT_100062d0,&uStack_90,2);
    iVar9 = iStack_84;
    puVar7 = PTR_DAT_1000630c;
    puVar6 = PTR_DAT_10006304;
    puVar5 = PTR_DAT_100062fc;
    puVar4 = PTR_DAT_100062e4;
    if (iVar8 != 10) break;
    uVar16 = uVar16 & 0xffffcfff;
    iVar9 = FUN_10017d28(PTR_DAT_100062dc,0xf,1,auStack_70,0);
    if (iVar9 == 0) {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000f068(PTR_DAT_100062e4,auStack_70[0]);
    }
  }
  switch(uStack_90) {
  case 1:
    if (*PTR_DAT_100062fc == '\0') {
      *(undefined2 *)PTR_DAT_10006300 = 0;
      *(undefined1 *)(iStack_84 + 0x69) = 1;
      *(undefined1 *)(iStack_84 + 0x6b) = 0;
      if (*(int *)puVar4 == 0) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_1000f164(iStack_84);
      }
      uVar16 = uVar16 & 0xffffcfff;
      iVar8 = FUN_10013140(0x10,1);
      puVar4 = PTR_DAT_100062e4;
      *(int *)(iVar8 + 0xc) = iStack_84;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10013000(puVar4,iVar8);
      *(undefined1 *)(iVar9 + 0x68) = 0;
      *(undefined1 *)(iVar9 + 0x6a) = 0;
      *(undefined4 *)(iVar9 + 0x70) = 0;
      *(undefined4 *)(iVar9 + 0x74) = 0;
      goto switchD_1000e461_caseD_4;
    }
    break;
  case 2:
    if (*PTR_DAT_100062fc == '\x01') {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000eff8();
      *puVar5 = 0;
    }
    else if ((*(int *)(PTR_DAT_100062e4 + 4) != 0) &&
            (iVar9 = *(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc), iVar9 != 0)) {
      *(undefined1 *)(iVar9 + 0x69) = 0;
      *(undefined1 *)(iVar9 + 0x68) = 1;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000eeb8();
    }
    goto switchD_1000e461_caseD_4;
  case 3:
    if (*PTR_DAT_100062fc == '\0') {
      iVar8 = *(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc);
      uVar16 = uVar16 & 0xffffcfff;
      iVar9 = FUN_10013140(0x10,1);
      *(int *)(iVar9 + 0xc) = iStack_84;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10013000(iVar8 + 0x70,iVar9);
      goto switchD_1000e461_caseD_4;
    }
    break;
  default:
    goto switchD_1000e461_caseD_4;
  case 5:
    if (*PTR_DAT_100062fc == '\0') {
      sVar1 = *(short *)PTR_DAT_10006300;
      iVar8 = *(int *)(*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x74) + 0xc);
      *(short *)PTR_DAT_10006300 = sVar1 + 1;
      *(short *)(iStack_84 + 0x7a) = sVar1;
      *(undefined2 *)(iStack_84 + 0x4c) = 0;
      *(undefined2 *)(iStack_84 + 0x48) = 0;
      *(undefined2 *)(iStack_84 + 0x72) = 0;
      *(undefined2 *)(iStack_84 + 0x4a) = 0;
      *(undefined1 *)(iStack_84 + 0x78) = 0;
      uVar16 = uVar16 & 0xffffcfff;
      uVar10 = FUN_10011178(0x24);
      *(undefined1 *)(iVar9 + 0x75) = uVar10;
      *(int *)(iVar8 + 0x48) = iVar9;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000f280(iVar9);
      goto switchD_1000e461_caseD_4;
    }
    break;
  case 6:
    if ((((*PTR_DAT_100062fc == '\0') && (*(int *)(PTR_DAT_100062e4 + 4) != 0)) &&
        (iVar9 = *(int *)(*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x74) + 0xc),
        iVar9 != 0)) && (iVar9 = *(int *)(iVar9 + 0x48), iVar9 != 0)) {
      if (*(short *)(iVar9 + 0xc) == 0) {
        *(undefined2 *)(iVar9 + 0xc) = 1;
      }
      *(undefined1 *)(iVar9 + 0x78) = 1;
      if (((*(short *)(iVar9 + 0x72) != 1) && (*(int *)PTR_DAT_10006308 == 0)) &&
         (*(short *)PTR_DAT_100062e8 != 0)) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_1000ed90();
      }
      goto switchD_1000e461_caseD_4;
    }
    break;
  case 8:
  case 0x2b:
    if (*PTR_DAT_100062fc == '\0') {
      if (uStack_8c == 3) {
        iVar9 = *(int *)(*(int *)(*(int *)(*(int *)(*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4)
                                                                     + 0xc) + 0x74) + 0xc) + 0x48) +
                                 0x54) + 0xc);
      }
      else {
        iVar9 = 0;
      }
      *(undefined2 *)(iVar9 + 0x4c) = 1;
    }
    goto switchD_1000e461_caseD_4;
  case 9:
switchD_1000e461_caseD_9:
    if (*PTR_DAT_100062fc == '\0') {
      if (*(int *)(PTR_DAT_100062e4 + 4) != 0) {
        iVar9 = *(int *)(*(int *)(*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x74) +
                                 0xc) + 0x48);
        if (*(short *)(iVar9 + 0xc) == 0) {
          *(undefined2 *)(iVar9 + 0xc) = 1;
        }
        *(undefined2 *)(*(int *)(iStack_84 + 0xc) + 0x4e) = *(undefined2 *)(iVar9 + 0xc);
        if ((*(char *)(iVar9 + 0x75) == '\x01') &&
           (*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x60) != 1)) {
          *(short *)(*(int *)(iStack_84 + 0xc) + 0x4e) =
               *(short *)(*(int *)(iStack_84 + 0xc) + 0x4e) << 1;
        }
        if (*(short *)(iVar9 + 0x72) == 1) {
          *(undefined2 *)(*(int *)(iStack_84 + 0xc) + 0x4e) = 1;
        }
        *(undefined2 *)(iVar9 + 0x4e) = *(undefined2 *)(*(int *)(iStack_84 + 0xc) + 0x4e);
        if (*(short *)(iVar9 + 0x72) == 1) {
          uStack_3c = rsil(1);
        }
        if (uStack_8c == 3) {
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013000(iVar9 + 0x50,iStack_84);
          puVar4 = PTR_DAT_10006304;
          if (*(short *)(iVar9 + 0x36) == 0) {
            *(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);
            *(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar4 + 8);
            *(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar4 + 0xc);
            *(undefined *)(iVar9 + 0x90) = puVar4[0x13];
          }
        }
        if (*(short *)(iVar9 + 0x72) == 1) {
          wsr((char)uVar16,uStack_3c);
          rsync();
        }
        goto switchD_1000e461_caseD_4;
      }
      if (*(int *)(iStack_84 + 0x50) != 2) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408(*(undefined4 *)(iStack_84 + 0x54));
      }
    }
    else {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10013408(*(undefined4 *)(*(int *)(iStack_84 + 0xc) + 0x54));
    }
    break;
  case 0xf:
    if (*(int *)PTR_DAT_10006308 == 0) {
      *PTR_DAT_1000630c = 0;
      iVar9 = *(int *)PTR_DAT_100062e4;
      *(uint *)PTR_DAT_10006310 = uStack_8c | DAT_10005e34;
      puVar4 = PTR_DAT_10006314;
      if (iVar9 != 0) {
        iVar8 = *(int *)(iVar9 + 0xc);
        *PTR_DAT_10006314 = 0;
        iVar9 = 0;
        if (*(int *)(iVar8 + 0x70) != 0) {
          iVar15 = *(int *)(*(int *)(iVar8 + 0x70) + 0xc);
          iVar9 = *(int *)(iVar15 + 0x4c);
          if (*(int *)(iVar15 + 0x48) != 0) {
            iVar9 = *(int *)(iVar15 + 0x48);
          }
          if (iVar9 != 0) {
            *puVar4 = *(undefined1 *)(iVar9 + 0x75);
          }
          if (((iVar15 != 0) && (iVar9 != 0)) && (*(short *)(iVar9 + 0x48) != 0)) {
            uStack_90 = 0xf;
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013658(1,&uStack_90);
            *PTR_DAT_1000630c = 1;
          }
        }
        iVar15 = *(int *)(iVar8 + 0x60);
        *(uint *)PTR_DAT_10006308 = uStack_8c;
        if (iVar15 == 1) {
          uStack_88 = (uint)(byte)*PTR_DAT_10006314;
          if ((iVar9 != 0) && (*(short *)(iVar9 + 0x4a) == 0)) {
            uStack_88 = 1;
          }
          if ((*(int *)PTR_DAT_10006308 == 2) || (*(int *)PTR_DAT_10006308 == 4)) {
            uStack_88 = 0;
          }
          *PTR_DAT_10006318 = (undefined1)uStack_88;
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013658(*(undefined4 *)(iVar8 + 100),&uStack_90);
          *PTR_DAT_1000630c = *PTR_DAT_1000630c + '\x01';
        }
        cVar11 = *PTR_DAT_1000630c;
        *PTR_DAT_1000631c = 0;
        if (cVar11 == '\0') {
          uStack_80 = 0x25;
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013658(3,&uStack_80);
        }
      }
    }
    goto switchD_1000e461_caseD_4;
  case 0x11:
    iVar9 = *(int *)(*(int *)PTR_DAT_100062e4 + 0xc);
    *(short *)(iVar9 + 0x6c) = *(short *)(iVar9 + 0x6c) + 1;
    piVar12 = *(int **)(*(int *)(*(int *)puVar4 + 0xc) + 0x70);
    if (*(int *)(iVar9 + 0x60) == 1) {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10013658(*(undefined4 *)(iVar9 + 100),&uStack_90);
    }
    if (*(int *)(iVar9 + 0x5c) == 1) {
      uStack_80 = 0x31;
      uStack_7c = (uint)*(ushort *)(iVar9 + 0x6c);
      uStack_78 = *(undefined4 *)(iVar9 + 0x58);
      uStack_74 = *(undefined4 *)(iVar9 + 0x48);
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10013658(10,&uStack_80);
    }
    if (*(int *)(iVar9 + 0x5c) != 6) {
      uStack_50 = 6;
      piStack_4c = &iStack_40;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10010f54(&uStack_50);
      iStack_40 = iStack_40 + 1;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_10010fd0(&uStack_50);
    }
    iVar8 = 0;
    while (((piVar12 != (int *)0x0 && (iVar8 = piVar12[3], *(int *)(iVar8 + 0x4c) != iStack_84)) &&
           (*(int *)(iVar8 + 0x48) != iStack_84))) {
      piVar12 = (int *)*piVar12;
    }
    if (*(int *)(iVar8 + 0x4c) != 0) {
      if (*(int *)(iVar9 + 0x5c) != 6) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_1000ef90();
      }
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000f128(*(undefined4 *)(iVar8 + 0x4c));
      *(short *)(*(int *)(iVar8 + 0x4c) + 0x4c) = *(short *)(*(int *)(iVar8 + 0x4c) + 0x4c) + 1;
      if (*(short *)(*(int *)(iVar8 + 0x4c) + 0xc) == *(short *)(*(int *)(iVar8 + 0x4c) + 0x4c)) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408();
        *(undefined4 *)(iVar8 + 0x4c) = 0;
      }
    }
    if (*(int *)(iVar8 + 0x48) == 0) {
LAB_1000e856:
      if (*(int *)(iVar8 + 0x4c) == 0) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013050(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70);
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408();
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408(iVar8);
      }
    }
    else {
      if (*(int *)(iVar9 + 0x5c) != 6) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_1000ef90();
      }
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000f128(*(undefined4 *)(iVar8 + 0x48));
      *(short *)(*(int *)(iVar8 + 0x48) + 0x4c) = *(short *)(*(int *)(iVar8 + 0x48) + 0x4c) + 1;
      if (*(short *)(*(int *)(iVar8 + 0x48) + 0xc) == *(short *)(*(int *)(iVar8 + 0x48) + 0x4c)) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408();
        *(undefined4 *)(iVar8 + 0x48) = 0;
      }
      if (*(int *)(iVar8 + 0x48) == 0) goto LAB_1000e856;
    }
    iVar9 = *(int *)PTR_DAT_10006308;
    *(short *)PTR_DAT_100062e8 = *(short *)PTR_DAT_100062e8 + 1;
    if (iVar9 == 0) {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000ed90();
    }
    if (*(char *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x68) != '\0') {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000eeb8();
    }
    goto switchD_1000e461_caseD_4;
  case 0x21:
    if (*(int *)PTR_DAT_100062e4 == *(int *)(PTR_DAT_100062e4 + 4)) {
      iVar9 = *(int *)(*(int *)PTR_DAT_100062e4 + 0xc);
      if ((*(int *)(iVar9 + 0x70) == *(int *)(iVar9 + 0x74)) &&
         (((iVar8 = *(int *)(*(int *)(iVar9 + 0x70) + 0xc), *(int *)(iVar8 + 0x48) == 0 ||
           (*(int *)(iVar8 + 0x4c) == 0)) &&
          (iVar9 = *(int *)(*(int *)(*(int *)(iVar9 + 0x74) + 0xc) + 0x48),
          *(short *)(iVar9 + 0x48) == 0)))) {
        uVar16 = uVar16 & 0xffffcfff;
        FUN_1000f0a8(iVar9 + 0x50,3);
        if (*(int *)PTR_DAT_10006308 == 0) {
          uStack_90 = 0xb;
          *(undefined2 *)(iVar9 + 0x48) = 1;
          *(undefined2 *)(iVar9 + 0xc) = 1;
          *(undefined2 *)(iVar9 + 0x72) = 1;
          uVar16 = uVar16 & 0xffffcfff;
          iStack_84 = iVar9;
          FUN_10013658(1,&uStack_90);
        }
      }
    }
    goto switchD_1000e461_caseD_4;
  case 0x25:
    if ((*(int *)PTR_DAT_10006308 != 0) &&
       ((iStack_38 = *(int *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x60), iStack_38 != 1 ||
        (cVar11 = *PTR_DAT_1000631c, *PTR_DAT_1000631c = cVar11 + 1U,
        (byte)*puVar7 <= (byte)(cVar11 + 1U))))) {
      iVar9 = *(int *)PTR_DAT_10006308;
      *PTR_DAT_1000630c = 0;
      if (iVar9 == 2) {
        uStack_80 = 0x30;
        uStack_7c = 0;
        uStack_78 = *(undefined4 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x58);
        uStack_74 = *(undefined4 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x48);
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013658(10,&uStack_80);
      }
      cVar11 = '\0';
      bVar2 = false;
      cStack_21 = '\0';
      piVar13 = (int *)*(int *)PTR_DAT_100062e4;
      piVar12 = (int *)PTR_DAT_100062e4;
joined_r0x1000ea5e:
      piVar3 = piVar13;
      PTR_DAT_100062e4 = (undefined *)piVar12;
      if ((piVar3 != (int *)0x0) && (cVar11 != '\x02')) {
        piVar12 = *(int **)(piVar3[3] + 0x70);
        do {
          if ((piVar12 == (int *)0x0) || (cVar11 == '\x02')) goto LAB_1000ead8;
          iVar9 = piVar12[3];
          if (*(int *)(iVar9 + 0x48) != 0) {
            uVar16 = uVar16 & 0xffffcfff;
            iVar8 = FUN_1000f030();
            if (iVar8 == 0) {
              bVar2 = true;
              *(undefined4 *)(iVar9 + 0x48) = 0;
            }
            cVar11 = cVar11 + '\x01';
            if (cVar11 == '\x02') goto LAB_1000ead8;
            *(undefined2 *)(*(int *)(iVar9 + 0x48) + 0x72) = 0;
          }
          if (*(int *)(iVar9 + 0x4c) != 0) {
            uVar16 = uVar16 & 0xffffcfff;
            iVar8 = FUN_1000f030();
            if (iVar8 == 0) {
              bVar2 = true;
              *(undefined4 *)(iVar9 + 0x4c) = 0;
            }
            cVar11 = cVar11 + '\x01';
            *(undefined2 *)(*(int *)(iVar9 + 0x4c) + 0x72) = 0;
          }
          piVar12 = (int *)*piVar12;
          if ((*(int *)(iVar9 + 0x48) == 0) && (*(int *)(iVar9 + 0x4c) == 0)) {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013050(piVar3[3] + 0x70);
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013408();
            bVar2 = true;
          }
        } while( true );
      }
      if (*(int *)PTR_DAT_10006308 == 4) {
        if (((!bVar2) && (*piVar12 != 0)) &&
           (iVar9 = *(int *)(*(int *)(*piVar12 + 0xc) + 0x70), iVar9 != 0)) {
          uVar16 = uVar16 & 0xffffcfff;
          FUN_1000efd8(*(undefined4 *)(iVar9 + 0xc));
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013050(*(int *)(*piVar12 + 0xc) + 0x70);
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013408();
        }
        if (((*(int *)PTR_DAT_10006308 == 4) &&
            (*(int *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70) == 0)) &&
           (*(char *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x69) == '\0')) {
          *(undefined1 *)(piVar3[3] + 0x6a) = 2;
          uVar16 = uVar16 & 0xffffcfff;
          FUN_1000eff8();
        }
      }
      puVar4 = PTR_DAT_100062e4;
      if ((*(int *)PTR_DAT_10006308 == 2) && (cStack_21 == '\0')) {
        *(undefined1 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x6a) = 2;
        if (*(char *)(*(int *)(*(int *)puVar4 + 0xc) + 0x69) == '\x01') {
          *PTR_DAT_100062fc = 1;
        }
        piVar12 = *(int **)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70);
        while (piVar12 != (int *)0x0) {
          uVar14 = piVar12[3];
          uVar16 = uVar16 & 0xffffcfff;
          FUN_1000efd8(uVar14);
          piVar12 = (int *)*piVar12;
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013408(uVar14);
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013050(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70);
          uVar16 = uVar16 & 0xffffcfff;
          FUN_10013408();
        }
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013050(PTR_DAT_100062e4);
        uVar16 = uVar16 & 0xffffcfff;
        FUN_10013408();
        puVar4 = PTR_DAT_100062e8;
        *(undefined4 *)PTR_DAT_10006308 = 0;
        *(undefined2 *)puVar4 = 0x14;
      }
      if (iStack_38 == 1) {
        if (*PTR_DAT_10006318 == '\x01') {
          piVar12 = *(int **)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70);
          while (piVar12 != (int *)0x0) {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1000efd8(piVar12[3]);
            piVar12 = (int *)*piVar12;
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013050(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x70);
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013408();
          }
        }
        if (iStack_38 == 1) {
          if (*PTR_DAT_10006318 == '\x01') {
            uStack_90 = 0x46;
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013658(*(undefined4 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 100),&uStack_90)
            ;
          }
          else {
            *PTR_DAT_100062fc = 0;
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1000eff8();
          }
        }
      }
      *(undefined2 *)PTR_DAT_100062e8 = 0x14;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000ee6c();
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000ed90();
      *(undefined4 *)PTR_DAT_10006308 = 0;
    }
    goto switchD_1000e461_caseD_4;
  case 0x29:
    if (*PTR_DAT_100062fc == '\0') {
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1001b38c(PTR_DAT_10006304,iStack_84,0x14);
    }
    break;
  case 0x2a:
    if (*PTR_DAT_100062fc == '\0') {
      iVar9 = *(int *)(*(int *)(*(int *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x74) +
                               0xc) + 0x48);
      *(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);
      *(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar6 + 8);
      *(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar6 + 0xc);
      *(undefined *)(iVar9 + 0x90) = puVar6[0x13];
      goto switchD_1000e461_caseD_9;
    }
    uVar16 = uVar16 & 0xffffcfff;
    FUN_10013408(*(undefined4 *)(*(int *)(iStack_84 + 0xc) + 0x54));
    break;
  case 0x33:
    if (*(int *)PTR_DAT_10006308 == 0) {
      if (*(int *)(PTR_DAT_100062e4 + 4) == 0) {
        *PTR_DAT_100062fc = 0;
      }
      else {
        iVar9 = *(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc);
        *(undefined1 *)(iVar9 + 0x6a) = 1;
        if (*(int *)(iVar9 + 0x74) != 0) {
          iVar8 = *(int *)(*(int *)(iVar9 + 0x74) + 0xc);
          if ((*(int *)(iVar8 + 0x4c) == 0) || (*(short *)(*(int *)(iVar8 + 0x4c) + 0x48) != 0)) {
            if ((*(int *)(iVar8 + 0x48) != 0) && (*(short *)(*(int *)(iVar8 + 0x48) + 0x48) == 0)) {
              uVar16 = uVar16 & 0xffffcfff;
              FUN_1000efbc();
              *(undefined4 *)(iVar8 + 0x48) = 0;
            }
          }
          else {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1000efbc();
            *(undefined4 *)(iVar8 + 0x4c) = 0;
          }
          if ((*(int *)(iVar8 + 0x4c) == 0) && (*(int *)(iVar8 + 0x48) == 0)) {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1001307c(iVar9 + 0x70);
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013408();
          }
        }
        if (*(int *)(iVar9 + 0x70) == 0) {
          if (*(char *)(iVar9 + 0x6b) == '\x01') {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1000eeb8(iVar9);
          }
          else {
            uVar16 = uVar16 & 0xffffcfff;
            FUN_1001307c(PTR_DAT_100062e4);
            uVar16 = uVar16 & 0xffffcfff;
            FUN_10013408();
          }
        }
        else {
          *(undefined1 *)(iVar9 + 0x68) = 1;
        }
        *(undefined1 *)(iVar9 + 0x69) = 0;
        *PTR_DAT_100062fc = 0;
      }
    }
    else if (*(int *)(PTR_DAT_100062e4 + 4) != 0) {
      *(undefined1 *)(*(int *)(*(int *)(PTR_DAT_100062e4 + 4) + 0xc) + 0x69) = 0;
    }
    goto switchD_1000e461_caseD_4;
  }
  uVar16 = uVar16 & 0xffffcfff;
  FUN_10013408(iStack_84);
  goto switchD_1000e461_caseD_4;
LAB_1000ead8:
  piVar13 = (int *)*piVar3;
  piVar12 = (int *)PTR_DAT_100062e4;
  if ((*(int *)(piVar3[3] + 0x70) == 0) && ((iStack_38 != 1 || (*PTR_DAT_10006318 != '\x01')))) {
    cStack_21 = '\x01';
    if (*(int *)PTR_DAT_10006308 != 2) {
      *(undefined1 *)(piVar3[3] + 0x6a) = 2;
      uVar16 = uVar16 & 0xffffcfff;
      FUN_1000ed4c(piVar3);
    }
    uVar16 = uVar16 & 0xffffcfff;
    FUN_10013050(PTR_DAT_100062e4);
    uVar16 = uVar16 & 0xffffcfff;
    FUN_10013408();
    bVar2 = true;
    piVar12 = (int *)PTR_DAT_100062e4;
  }
  goto joined_r0x1000ea5e;
}


