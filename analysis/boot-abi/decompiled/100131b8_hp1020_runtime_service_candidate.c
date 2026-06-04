/* Function: 100131b8 hp1020_runtime_service_candidate */


/* WARNING: Control flow encountered bad instruction data */

undefined4 * hp1020_runtime_service_candidate(uint param_1,int param_2)

{
  bool bVar1;
  undefined *puVar2;
  undefined4 uVar3;
  undefined *puVar4;
  undefined *puVar5;
  undefined4 unaff_retaddr;
  undefined4 *puVar6;
  undefined4 *puVar7;
  uint uVar8;
  int iVar9;
  uint uVar10;
  uint uVar11;
  
  memw();
  *(undefined4 *)PTR_DAT_100066bc = unaff_retaddr;
  uVar3 = DAT_100066ac;
  if ((param_1 & 3) != 0) {
    param_1 = ((param_1 >> 2) + 1) * 4;
  }
  if ((param_2 == 0) || (param_2 == 2)) {
    param_1 = (param_1 - (param_1 & 0xf)) + 0x1c;
  }
  puVar6 = *(undefined4 **)PTR_DAT_10006698;
  threadx_memory_or_copy_candidate(DAT_100066ac,0xffffffff);
  puVar2 = PTR_DAT_1000669c;
  bVar1 = true;
  if (((int)((*(int *)PTR_DAT_100066a8 + -0xc) - param_1) <= DAT_100066c0) &&
     ((param_2 == 0 || ((param_2 == 1 && (DAT_10005ddc < param_1)))))) {
    hp1020_sys_interface_31_candidate(uVar3);
    return (undefined4 *)0x0;
  }
  if (param_2 == 0) {
    puVar6 = *(undefined4 **)PTR_DAT_1000669c;
  }
  do {
    if (-1 < (int)puVar6[2]) {
      do {
        puVar5 = PTR_DAT_100066bc;
        puVar4 = PTR_DAT_100066a8;
        uVar3 = DAT_100066a4;
        uVar8 = DAT_1000628c;
        uVar11 = puVar6[1];
        if (param_1 <= uVar11) {
          if (uVar11 - param_1 < 0x31) {
            uVar8 = (puVar6[2] | DAT_10005e34) & DAT_100066b8;
            puVar6[2] = uVar8;
            memw();
            uVar8 = uVar8 | *(uint *)puVar5 & DAT_10005eb0;
            puVar6[2] = uVar8;
            if (param_2 == 0) {
              uVar8 = uVar8 | DAT_100066c8;
              puVar6[2] = uVar8;
              if ((uVar8 & 0x40000000) == 0) {
                *(uint *)puVar2 = (int)puVar6 + uVar11 + 0xc;
              }
              else {
                *(undefined4 *)puVar2 = *(undefined4 *)PTR_DAT_10006698;
              }
              goto LAB_10013312;
            }
            uVar8 = uVar8 & DAT_100060c0;
          }
          else {
            *(uint *)((int)puVar6 + param_1 + 0x10) = (uVar11 - param_1) - 0xc;
            uVar11 = DAT_100066c4;
            uVar8 = *(uint *)((int)puVar6 + param_1 + 0x14) & uVar8;
            *(uint *)((int)puVar6 + param_1 + 0x14) = uVar8;
            uVar10 = puVar6[2];
            *(int *)PTR_DAT_100066a8 = *(int *)PTR_DAT_100066a8 + -0xc;
            *(uint *)((int)puVar6 + param_1 + 0x14) = uVar8 & uVar11 | (uVar10 >> 0x1e & 1) << 0x1e;
            uVar11 = DAT_100066b8;
            *(undefined4 *)((int)puVar6 + param_1 + 0xc) = uVar3;
            uVar8 = DAT_100066c4;
            puVar6[1] = param_1;
            puVar4 = PTR_DAT_100066bc;
            uVar11 = puVar6[2] & uVar8 & uVar11;
            puVar6[2] = uVar11;
            uVar8 = DAT_10005eb0;
            memw();
            uVar10 = *(uint *)puVar4;
            *puVar6 = uVar3;
            uVar8 = uVar11 | uVar10 & uVar8 | DAT_10005e34;
            puVar6[2] = uVar8;
            uVar11 = DAT_100066c8;
            if (param_2 == 0) {
              *(uint *)puVar2 = (int)puVar6 + param_1 + 0xc;
              uVar8 = uVar8 | uVar11;
            }
            else {
              uVar8 = uVar8 & DAT_100060c0;
            }
          }
          puVar6[2] = uVar8;
LAB_10013312:
          *(int *)PTR_DAT_100066a8 = *(int *)PTR_DAT_100066a8 - puVar6[1];
          if ((param_2 != 0) && (param_2 != 2)) {
            hp1020_sys_interface_31_candidate(DAT_100066ac);
            return puVar6 + 3;
          }
          puVar7 = puVar6 + 3;
          if (((uint)puVar7 & 0xf) != 0) {
            puVar7 = (undefined4 *)(((uint)puVar7 & 0xfffffff0) + 0x10);
          }
          if (puVar6 + 3 < puVar7) {
                    /* WARNING: Bad instruction - Truncating control flow here */
            halt_baddata();
          }
          hp1020_sys_interface_31_candidate(DAT_100066ac);
          return puVar7;
        }
        if (((puVar6[2] & 0x40000000) != 0) || (*(int *)((int)puVar6 + uVar11 + 0x14) < 0))
        goto LAB_100133c0;
        uVar10 = puVar6[2] & DAT_100066c4;
        iVar9 = *(int *)PTR_DAT_100066a8;
        puVar6[1] = uVar11 + 0xc + *(int *)((int)puVar6 + uVar11 + 0x10);
        uVar8 = *(uint *)((int)puVar6 + uVar11 + 0x14);
        *(int *)puVar4 = iVar9 + 0xc;
        puVar6[2] = uVar10 | (uVar8 >> 0x1e & 1) << 0x1e;
        iVar9 = *(int *)puVar2;
        *(undefined4 *)((int)puVar6 + uVar11 + 0xc) = 0;
        if ((int)puVar6 + uVar11 + 0xc == iVar9) {
          *(undefined4 **)puVar2 = puVar6;
        }
      } while( true );
    }
    if (param_2 == 0) {
      if ((puVar6[2] & 0x20000000) != 0) {
        hp1020_sys_interface_31_candidate(DAT_100066ac);
        return (undefined4 *)0x0;
      }
LAB_100133c0:
      if (param_2 != 0) goto LAB_100133e5;
      if ((puVar6 == *(undefined4 **)puVar2) && (!bVar1)) {
        hp1020_sys_interface_31_candidate(DAT_100066ac);
        return (undefined4 *)0x0;
      }
      if ((puVar6[2] & 0x40000000) == 0) goto LAB_100133f8;
      puVar6 = *(undefined4 **)PTR_DAT_10006698;
    }
    else {
LAB_100133e5:
      if ((puVar6[2] & 0x40000000) != 0) {
        hp1020_sys_interface_31_candidate(DAT_100066ac);
        return (undefined4 *)0x0;
      }
LAB_100133f8:
      puVar6 = (undefined4 *)((int)puVar6 + puVar6[1] + 0xc);
    }
    bVar1 = false;
  } while( true );
}


