/* Function: 10016b50 FUN_10016b50 */


uint FUN_10016b50(undefined4 *param_1,byte *param_2,undefined4 *param_3,int param_4)

{
  byte bVar1;
  bool bVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  byte *pbVar6;
  byte *pbVar7;
  uint uVar8;
  int iVar9;
  int iVar10;
  undefined1 in_b10;
  
  bVar2 = false;
  pbVar7 = param_2;
  do {
    pbVar6 = pbVar7;
    uVar8 = (uint)*pbVar6;
    pbVar7 = pbVar6 + 1;
  } while ((PTR_DAT_10005d68[uVar8] & 8) != 0);
  if (uVar8 == 0x2d) {
    bVar1 = *pbVar7;
    bVar2 = true;
  }
  else {
    if (uVar8 != 0x2b) goto LAB_10016b88;
    bVar1 = *pbVar7;
  }
  uVar8 = (uint)bVar1;
  pbVar7 = pbVar6 + 2;
LAB_10016b88:
  if ((((param_4 == 0) || (param_4 == 0x10)) && (uVar8 == 0x30)) &&
     ((*pbVar7 == 0x78 || (*pbVar7 == 0x58)))) {
    uVar8 = (uint)pbVar7[1];
    param_4 = 0x10;
    pbVar7 = pbVar7 + 2;
  }
  if ((param_4 == 0) && (param_4 = 10, uVar8 == 0x30)) {
    param_4 = 8;
  }
  uVar5 = DAT_1000628c;
  if (bVar2) {
    uVar5 = DAT_10005e34;
  }
  iVar3 = FUN_1001b6b0(uVar5,param_4);
  uVar4 = FUN_1001b668(uVar5,param_4);
  uVar5 = 0;
  iVar10 = 0;
  do {
    bVar1 = PTR_DAT_10005d68[uVar8];
    if ((bVar1 & 4) == 0) {
      if ((bVar1 & 3) == 0) {
LAB_10016c2d:
        if ((bool)in_b10) {
          uVar5 = DAT_1000628c;
          if (bVar2) {
            uVar5 = DAT_10005e34;
          }
          *param_1 = 0x22;
        }
        else if (bVar2) {
          uVar5 = -uVar5;
        }
        if (param_3 != (undefined4 *)0x0) {
          pbVar7 = pbVar7 + -1;
          if (iVar10 == 0) {
            pbVar7 = param_2;
          }
          *param_3 = pbVar7;
        }
        return uVar5;
      }
      if ((bVar1 & 1) == 0) {
        iVar9 = uVar8 - 0x57;
      }
      else {
        iVar9 = uVar8 - 0x37;
      }
    }
    else {
      iVar9 = uVar8 - 0x30;
    }
    if (param_4 <= iVar9) goto LAB_10016c2d;
    if (((iVar10 < 0) || (uVar4 < uVar5)) || ((uVar5 == uVar4 && (iVar3 < iVar9)))) {
      iVar10 = -1;
    }
    else {
      iVar10 = 1;
      uVar5 = uVar5 * param_4 + iVar9;
    }
    uVar8 = (uint)*pbVar7;
    pbVar7 = pbVar7 + 1;
  } while( true );
}


