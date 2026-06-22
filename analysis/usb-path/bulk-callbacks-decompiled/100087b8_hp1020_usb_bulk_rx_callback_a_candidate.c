
int hp1020_usb_bulk_rx_callback_a_candidate(int param_1,int param_2,int param_3)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  uint uVar5;
  uint uVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  undefined1 auStack_30 [4];
  int iStack_2c;
  
  iVar4 = param_1 + DAT_10005e34;
  iStack_2c = param_2;
  FUN_10017414(param_1,param_2);
  puVar1 = PTR_DAT_10005e5c;
  *(int *)PTR_DAT_10005e4c = iStack_2c;
  *(undefined4 *)puVar1 = 0;
  FUN_100171b0(4);
  if ((10 < param_3) && (*(int *)PTR_DAT_10005e50 < iStack_2c)) {
    *(int *)PTR_DAT_10005e54 = iVar4;
  }
  puVar2 = PTR_DAT_10005e3c;
  puVar1 = PTR_DAT_10005e38;
  iVar7 = *(int *)PTR_DAT_10005e4c;
  do {
    if (iVar7 < 1) {
      *(undefined4 *)PTR_DAT_10005e54 = 0;
      FUN_10017184(4);
      return iStack_2c - *(int *)PTR_DAT_10005e4c;
    }
    uVar5 = *(uint *)puVar1;
    if (uVar5 == 0) {
      memw();
      if ((*DAT_10005e68 & DAT_10005e6c) != 0) {
        memw();
        memw();
        *DAT_10005e70 = *DAT_10005e70 | 0x100;
      }
      FUN_10017184(4);
      iVar7 = FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1,auStack_30,param_3);
      if (iVar7 == 7) {
        iVar4 = *(int *)PTR_DAT_10005e4c;
        *(undefined4 *)PTR_DAT_10005e54 = 0;
        return iStack_2c - iVar4;
      }
      FUN_100171b0(4);
      if (*PTR_DAT_10005e48 == '\0') {
        uVar5 = *(uint *)PTR_DAT_10005e4c;
        if (*(uint *)puVar1 < *(uint *)PTR_DAT_10005e4c) {
          uVar5 = *(uint *)puVar1;
        }
        FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2,
                     uVar5);
        iVar7 = *(int *)PTR_DAT_10005e5c;
        iVar8 = *(int *)puVar2;
        *(uint *)PTR_DAT_10005e5c = iVar7 + uVar5;
        puVar3 = PTR_DAT_10005e4c;
        iVar9 = *(int *)puVar1;
        *(uint *)puVar2 = iVar8 + uVar5;
        iVar8 = *(int *)puVar3;
        *(uint *)puVar1 = iVar9 - uVar5;
        iVar8 = iVar8 - uVar5;
        *(int *)puVar3 = iVar8;
        if ((param_3 < 0xb) || (iVar8 <= *(int *)PTR_DAT_10005e50)) goto LAB_1000892c;
        iVar7 = iVar4 + iVar7 + uVar5;
        goto LAB_10008931;
      }
    }
    else {
      uVar6 = *(uint *)PTR_DAT_10005e4c;
      if (uVar5 < *(uint *)PTR_DAT_10005e4c) {
        uVar6 = uVar5;
      }
      FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2,uVar6)
      ;
      iVar7 = *(int *)PTR_DAT_10005e5c;
      iVar8 = *(int *)puVar2;
      *(uint *)PTR_DAT_10005e5c = iVar7 + uVar6;
      puVar3 = PTR_DAT_10005e4c;
      iVar9 = *(int *)puVar1;
      *(uint *)puVar2 = iVar8 + uVar6;
      iVar8 = *(int *)puVar3;
      *(uint *)puVar1 = iVar9 - uVar6;
      iVar8 = iVar8 - uVar6;
      *(int *)puVar3 = iVar8;
      if ((param_3 < 0xb) || (iVar8 <= *(int *)PTR_DAT_10005e50)) {
LAB_1000892c:
        iVar7 = 0;
      }
      else {
        iVar7 = iVar4 + iVar7 + uVar6;
      }
LAB_10008931:
      *(int *)PTR_DAT_10005e54 = iVar7;
    }
    if ((*(int *)puVar1 == 0) && (*PTR_DAT_10005e20 == '\0')) {
      *(undefined4 *)puVar2 = 0;
      puVar3 = PTR_DAT_10005e78;
      *(undefined4 *)PTR_DAT_10005e40 = 0;
      *puVar3 = 0;
      FUN_100086f4(0);
      memw();
      if ((*DAT_10005e68 & DAT_10005e6c) != 0) {
        memw();
        memw();
        *DAT_10005e70 = *DAT_10005e70 | 0x100;
      }
    }
    iVar7 = *(int *)PTR_DAT_10005e4c;
  } while( true );
}

