
uint hp1020_usb_transfer_callback_a_candidate(int param_1,int param_2,uint param_3,uint param_4)

{
  bool bVar1;
  undefined4 uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  int iVar6;
  undefined1 in_b3;
  int iStack_28;
  uint uStack_24;
  
  uStack_24 = 0;
  if (param_4 == 1) {
    iStack_28 = 0x32;
  }
  else if (param_4 == 0) {
    uVar3 = FUN_10011178(9);
    if ((uVar3 & 0xff) < 5) {
      iStack_28 = 500;
    }
    else {
      iStack_28 = (uVar3 & 0xff) * 100;
    }
  }
  else if (param_4 == 2) {
    iStack_28 = 0;
  }
  else if (param_4 == 3) {
    iStack_28 = 200;
  }
  uVar3 = 0;
  uVar4 = *(uint *)(param_1 + 0x24);
  if (uVar4 != 0) {
    uVar3 = param_3;
    if (uVar4 <= param_3) {
      uVar3 = uVar4;
    }
    FUN_1001b38c(param_2,*(undefined4 *)(param_1 + 0x20),uVar3);
    iVar6 = *(int *)(param_1 + 0x24) - uVar3;
    *(int *)(param_1 + 0x24) = iVar6;
    *(uint *)(param_1 + 0x20) = *(int *)(param_1 + 0x20) + uVar3;
    if ((iVar6 == 0) && (DAT_10005ddc < *(uint *)(param_1 + 0x28))) {
      FUN_10013408(*(undefined4 *)(param_1 + 0x1c));
      uVar2 = FUN_10013140(0x400,1);
      *(undefined4 *)(param_1 + 0x1c) = uVar2;
      *(undefined4 *)(param_1 + 0x28) = 0x400;
      *(undefined4 *)(param_1 + 0x20) = uVar2;
    }
  }
  bVar1 = false;
  uVar4 = 0;
  uVar5 = *(uint *)(param_1 + 0x3c);
  if (uVar5 != 0) {
    if (uVar3 == 0) {
      *(undefined4 *)(param_1 + 0x3c) = 0;
      uVar3 = uVar5;
    }
    return uVar3;
  }
  if (uVar3 < param_3) {
    do {
      uVar4 = (**(code **)(param_1 + 4))(param_2 + uVar3,param_3 - uVar3,iStack_28);
      if ((int)uVar4 < 0) {
LAB_100081df:
        bVar1 = true;
      }
      else {
        uVar3 = uVar3 + uVar4;
        if (param_4 == 1) {
          uStack_24 = uStack_24 + iStack_28;
          if ((uVar3 != 0) || (DAT_10005de0 < uStack_24)) goto LAB_100081df;
        }
        else if ((param_4 == 0) || (param_4 < 4)) goto LAB_100081df;
      }
    } while (!bVar1);
  }
  uVar5 = uVar3;
  if (((bool)in_b3) && (uVar5 = uVar4, uVar3 != 0)) {
    *(uint *)(param_1 + 0x3c) = uVar4;
    uVar5 = uVar3;
  }
  return uVar5;
}

