/* Function: 10016ef8 FUN_10016ef8 */


/* WARNING: Removing unreachable block (ram,0x10017139) */

undefined1  [16]
FUN_10016ef8(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            undefined4 param_5,undefined4 param_6)

{
  uint uVar2;
  ulonglong uVar1;
  undefined *puVar3;
  undefined4 unaff_retaddr;
  undefined4 uVar4;
  uint uVar5;
  int iVar6;
  undefined1 *puVar7;
  uint uVar9;
  undefined4 uVar10;
  undefined1 auVar8 [16];
  uint uVar11;
  int iVar12;
  uint unaff_a8;
  uint unaff_a9;
  uint unaff_a10;
  uint unaff_a11;
  uint in_a12;
  uint in_a13;
  uint in_a14;
  uint in_a15;
  undefined1 in_LBEG;
  undefined1 in_LEND;
  undefined1 in_LCOUNT;
  int in_SAR;
  undefined1 in_EPC1;
  undefined1 in_EXCSAVE1;
  undefined1 in_EXCVADDR;

  puVar3 = PTR_DAT_10006a74;
  *(undefined4 *)PTR_DAT_10006a74 = unaff_retaddr;
  *(undefined4 *)(puVar3 + 4) = param_1;
  uVar5 = rsr(in_EPC1);
  uVar4 = rsr(in_EXCSAVE1);
  *(undefined4 *)(puVar3 + 0xc) = param_3;
  uVar10 = rsr((char)in_SAR);
  *(undefined4 *)(puVar3 + 0x10) = param_4;
  *(undefined4 *)(puVar3 + 0x14) = param_5;
  *(undefined4 *)(puVar3 + 0x18) = param_6;
  *(undefined4 *)(puVar3 + 8) = uVar4;
  *(undefined4 *)(puVar3 + 0x1c) = uVar10;
  uVar9 = rsr(in_EXCVADDR);
  if ((uVar9 & 3) != 0) {
    in_SAR = (uVar5 & 3) * -8 + 0x20;
    uVar2 = (uint)(*(ulonglong *)(uVar5 & 0xfffffffc) >> in_SAR);
    uVar9 = uVar2 >> 0x1c;
    if (uVar9 == 8) {
      iVar12 = uVar5 + 2;
    }
    else {
      if ((uVar9 != 2) ||
         (((uVar11 = uVar2 >> 0x10 & 0xf, uVar11 != 2 && (uVar11 != 1)) && (uVar11 != 9)))) {
        iVar12 = 9;
        if (uVar9 == 9) {
          iVar12 = uVar5 + 2;
        }
        else if (uVar9 == 2) {
          uVar9 = uVar2 >> 0x10 & 0xf;
          if ((uVar9 != 6) && (uVar9 != 5)) goto LAB_10017030;
          iVar12 = uVar5 + 3;
        }
        iVar6 = rsr(in_LEND);
        if ((iVar6 == iVar12) && (iVar6 = rsr(in_LCOUNT), iVar6 != 0)) {
          wsr(in_LCOUNT,iVar6 + -1);
          iVar12 = rsr(in_LBEG);
        }
        wsr(in_EPC1,iVar12);
        uVar5 = uVar2 >> 0x18 & 0xf;
        switch(uVar5) {
        case 0:
          uVar5 = *(uint *)puVar3;
          break;
        case 1:
          break;
        case 2:
          uVar5 = *(uint *)(puVar3 + 4);
          break;
        case 3:
          uVar5 = *(uint *)(puVar3 + 8);
          break;
        case 4:
          uVar5 = *(uint *)(puVar3 + 0xc);
          break;
        case 5:
          uVar5 = *(uint *)(puVar3 + 0x10);
          break;
        case 6:
          uVar5 = *(uint *)(puVar3 + 0x14);
          break;
        case 7:
          uVar5 = *(uint *)(puVar3 + 0x18);
          break;
        case 8:
          uVar5 = unaff_a8;
          break;
        case 9:
          uVar5 = unaff_a9;
          break;
        case 10:
          uVar5 = unaff_a10;
          break;
        case 0xb:
          uVar5 = unaff_a11;
          break;
        case 0xc:
          uVar5 = in_a12;
          break;
        case 0xd:
          uVar5 = in_a13;
          break;
        case 0xe:
          uVar5 = in_a14;
          break;
        case 0xf:
          uVar5 = in_a15;
        }
        puVar7 = (undefined1 *)rsr(in_EXCVADDR);
        if ((uVar2 >> 0x1c == 9) || ((uVar2 >> 0x10 & 0xf) != 5)) {
          puVar7[3] = (char)uVar5;
          puVar7[2] = (char)(uVar5 >> 8);
          uVar5 = uVar5 >> 0x10;
        }
        puVar7[1] = (char)uVar5;
        *puVar7 = (char)(uVar5 >> 8);
        goto LAB_10017030;
      }
      iVar12 = uVar5 + 3;
    }
    iVar6 = rsr(in_LEND);
    if ((iVar6 == iVar12) && (iVar6 = rsr(in_LCOUNT), iVar6 != 0)) {
      wsr(in_LCOUNT,iVar6 + -1);
      iVar12 = rsr(in_LBEG);
    }
    wsr(in_EPC1,iVar12);
    uVar5 = rsr(in_EXCVADDR);
    in_SAR = (uVar5 & 3) * -8 + 0x20;
    uVar1 = *(ulonglong *)(uVar5 & 0xfffffffc) >> in_SAR;
    uVar5 = (uint)uVar1;
    if (uVar2 >> 0x1c != 8) {
      uVar9 = uVar2 >> 0x10 & 0xf;
      if (uVar9 == 1) {
        uVar5 = uVar5 >> 0x10;
      }
      else if (uVar9 == 9) {
        in_SAR = 0x10;
        uVar5 = (uint)(short)(uVar1 >> 0x10);
      }
    }
    switch(uVar2 >> 0x18 & 0xf) {
    case 0:
      *(uint *)puVar3 = uVar5;
      break;
    case 1:
      break;
    case 2:
      *(uint *)(puVar3 + 4) = uVar5;
      break;
    case 3:
      *(uint *)(puVar3 + 8) = uVar5;
      break;
    case 4:
      *(uint *)(puVar3 + 0xc) = uVar5;
      break;
    case 5:
      *(uint *)(puVar3 + 0x10) = uVar5;
      break;
    case 6:
      *(uint *)(puVar3 + 0x14) = uVar5;
      break;
    case 7:
      *(uint *)(puVar3 + 0x18) = uVar5;
      break;
    case 8:
      break;
    case 9:
      break;
    case 10:
      break;
    case 0xb:
      break;
    case 0xc:
      break;
    case 0xd:
      break;
    case 0xe:
      break;
    case 0xf:
    }
  }
LAB_10017030:
  wsr((char)in_SAR,*(undefined4 *)(puVar3 + 0x1c));
  rfe();
  auVar8._8_4_ = *(undefined4 *)(puVar3 + 8);
  auVar8._12_4_ = *(undefined4 *)(puVar3 + 4);
  auVar8._4_4_ = *(undefined4 *)(puVar3 + 0xc);
  auVar8._0_4_ = *(undefined4 *)(puVar3 + 0x10);
  return auVar8;
}
