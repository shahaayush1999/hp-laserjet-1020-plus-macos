/* Function: 10009d34 hp1020_task_entry_10009d34 */


undefined4 hp1020_task_entry_10009d34(int param_1)

{
  int iVar1;
  uint uVar2;
  undefined *puVar3;
  uint uVar4;
  undefined4 uVar5;
  uint uVar6;
  code *pcVar7;
  undefined *puVar8;
  undefined4 auStack_1d0 [88];
  uint uStack_70;
  char cStack_51;
  char cStack_41;
  undefined1 uStack_40;
  undefined *puStack_3c;
  undefined4 uStack_38;
  uint uStack_34;
  
  puVar3 = PTR_DAT_10005fe0;
  cStack_41 = '\0';
  cStack_51 = '\0';
  uStack_40 = 0;
  puStack_3c = (undefined *)0x0;
  uStack_38 = 0;
  uStack_70 = FUN_100169d4(PTR_DAT_10005fe0);
  puVar8 = PTR_DAT_10005ffc;
  iVar1 = (**(code **)(param_1 + 0xc))(param_1,PTR_DAT_10005ffc,uStack_70,0);
  if (iVar1 != uStack_70) {
    if (0 < iVar1) {
      (**(code **)(param_1 + 0x14))(param_1,puVar8,iVar1);
    }
    return 0;
  }
  iVar1 = func_0x1001b56c(puVar3,puVar8,uStack_70);
  if (iVar1 != 0) {
    (**(code **)(param_1 + 0x14))(param_1,puVar8,uStack_70);
    return 0;
  }
  func_0x1001262c(0);
  uStack_70 = 0x10;
  uVar2 = (**(code **)(param_1 + 0xc))(param_1,puVar8,0x10,0);
  puVar3 = (undefined *)0x0;
  if (uVar2 < uStack_70) {
    if ((int)uVar2 < 1) goto LAB_1000a23b;
    pcVar7 = *(code **)(param_1 + 0x14);
  }
  else {
    if (*(ushort *)(puVar8 + 0xe) == DAT_10006000) {
      do {
        puStack_3c = (undefined *)0x0;
        uStack_34 = (uint)*(ushort *)(PTR_DAT_10005ffc + 0xc);
        uVar6 = (*(int *)PTR_DAT_10005ffc + -0x10) - uStack_34;
        if (uStack_34 != 0) {
          puStack_3c = (undefined *)FUN_10013140(uStack_34,2);
        }
        puVar3 = (undefined *)0x0;
        if (uVar6 != 0) {
          puVar3 = (undefined *)FUN_10013140(uVar6,0);
        }
        if ((uStack_34 != 0) &&
           (uVar2 = (**(code **)(param_1 + 0xc))(param_1,puStack_3c,uStack_34,0), uVar2 != uStack_34
           )) {
          if ((int)uVar2 < 1) goto LAB_1000a23b;
          pcVar7 = *(code **)(param_1 + 0x14);
          puVar8 = puStack_3c;
          goto LAB_1000a238;
        }
        if ((uVar6 != 0) &&
           (uVar2 = (**(code **)(param_1 + 0xc))(param_1,puVar3,uVar6,0), uVar2 != uVar6)) {
          (**(code **)(param_1 + 0x14))(param_1,puStack_3c,uStack_34);
          if ((int)uVar2 < 1) goto LAB_1000a23b;
          pcVar7 = *(code **)(param_1 + 0x14);
          puVar8 = puVar3;
          goto LAB_1000a238;
        }
        uVar2 = *(uint *)(PTR_DAT_10005ffc + 4);
        uVar5 = *(undefined4 *)(PTR_DAT_10005ffc + 8);
        if (uVar2 != 1) {
          uVar4 = (**(code **)(param_1 + 0xc))(param_1,PTR_DAT_10005ffc,uStack_70,0);
          if (uVar4 < uStack_70) {
            if (0 < (int)uVar4) {
              pcVar7 = *(code **)(param_1 + 0x14);
LAB_1000a21c:
              (*pcVar7)(param_1,PTR_DAT_10005ffc,uVar4);
            }
            (**(code **)(param_1 + 0x14))(param_1,puVar3,uVar6);
            pcVar7 = *(code **)(param_1 + 0x14);
            puVar8 = puStack_3c;
            uVar2 = uStack_34;
            goto LAB_1000a238;
          }
          if (*(ushort *)(PTR_DAT_10005ffc + 0xe) != DAT_10006000) {
            pcVar7 = *(code **)(param_1 + 0x14);
            uVar4 = uStack_70;
            goto LAB_1000a21c;
          }
        }
        if (uVar2 < 0xd) {
                    /* WARNING: Could not recover jumptable at 0x10009efb. Too many branches */
                    /* WARNING: Treating indirect jump as call */
          uVar5 = (**(code **)(PTR_switchdataD_100036f0_1000600c + uVar2 * 4))(param_1,uVar5);
          return uVar5;
        }
        if (uStack_34 != 0) {
          FUN_10013408(puStack_3c);
        }
        if (cStack_51 != '\0') {
          return 0;
        }
      } while( true );
    }
    pcVar7 = *(code **)(param_1 + 0x14);
    uVar2 = uStack_70;
  }
LAB_1000a238:
  (*pcVar7)(param_1,puVar8,uVar2);
LAB_1000a23b:
  *(undefined4 *)PTR_DAT_10006010 = 1;
  if (puStack_3c != (undefined *)0x0) {
    FUN_10013408(puStack_3c);
  }
  if (puVar3 != (undefined *)0x0) {
    FUN_10013408(puVar3);
  }
  if (cStack_41 != '\0') {
    auStack_1d0[0] = 0x33;
    FUN_10013658(3,auStack_1d0);
  }
  FUN_100126b0(0);
  return 0xfffffffe;
}


