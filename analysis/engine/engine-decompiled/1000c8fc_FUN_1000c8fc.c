/* Function: 1000c8fc FUN_1000c8fc */


undefined4 FUN_1000c8fc(char param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined *puVar1;
  int iVar2;
  char cVar4;
  undefined4 uVar3;
  byte bVar5;
  int iVar6;
  uint uVar7;
  undefined1 in_b10;
  undefined4 local_b0;
  undefined2 *puStack_ac;
  undefined1 auStack_a0 [3];
  undefined1 uStack_9d;
  undefined1 auStack_9c [12];
  undefined1 auStack_90 [16];
  undefined1 auStack_80 [3];
  undefined1 uStack_7d;
  undefined1 auStack_7c [4];
  undefined1 auStack_78 [4];
  undefined2 auStack_74 [2];
  undefined1 auStack_70 [2];
  undefined2 uStack_6e;
  undefined4 uStack_6c;
  undefined1 auStack_68 [4];
  undefined4 uStack_64;
  undefined1 auStack_60 [4];
  undefined4 uStack_5c;
  undefined1 auStack_58 [4];
  int iStack_54;
  undefined1 auStack_50 [16];
  undefined4 uStack_40;
  undefined1 auStack_3c [3];
  undefined1 uStack_39;
  undefined1 auStack_38 [4];
  undefined4 uStack_34;
  int iStack_30;
  int iStack_2c;
  uint uStack_28;
  undefined4 uStack_24;
  
  puVar1 = PTR_DAT_10006148;
  uStack_24 = 0;
  bVar5 = 0;
  uVar7 = 0;
  while( true ) {
    iVar6 = *(int *)(puVar1 + uVar7 * 0x24);
    if (iVar6 == 0x14) {
      return uStack_24;
    }
    iVar2 = FUN_1001684c(param_3,*(int *)((int)(puVar1 + uVar7 * 0x24) + 4));
    if (iVar2 == 0) break;
    bVar5 = bVar5 + 1;
    uVar7 = (uint)bVar5;
    if (0x13 < uVar7) {
      return uStack_24;
    }
  }
  switch(iVar6) {
  case 0:
    cVar4 = FUN_1000c850(param_4,bVar5,auStack_3c);
    if (cVar4 != '\0') {
      return 1;
    }
    local_b0 = 10;
    puStack_ac = (undefined2 *)auStack_38;
    FUN_10010f54(&local_b0);
    auStack_38[0] = uStack_39;
    break;
  case 1:
    iVar6 = FUN_1000d5b0(param_4,&uStack_34);
    if (iVar6 != 0) {
      return 2;
    }
    if (uStack_34 < *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18)) {
      uStack_24 = 3;
      uStack_34 = *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18);
    }
    if (*(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c) < uStack_34) {
      uStack_24 = 3;
      uStack_34 = *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c);
    }
    local_b0 = 9;
    puStack_ac = (undefined2 *)auStack_38;
    FUN_10010f54(&local_b0);
    auStack_38[0] = (undefined1)uStack_34;
    break;
  case 2:
    uVar3 = FUN_1000c89c(bVar5,param_4);
    return uVar3;
  case 3:
    cVar4 = FUN_1000c850(param_4,bVar5,auStack_a0);
    if (cVar4 == '\0') {
      local_b0 = 0x25;
      puStack_ac = (undefined2 *)auStack_9c;
      FUN_10010f54(&local_b0);
      auStack_9c[0] = uStack_9d;
      FUN_10010fd0(&local_b0);
      return uStack_24;
    }
    return 1;
  case 4:
    local_b0 = 4;
    puStack_ac = (undefined2 *)auStack_90;
    FUN_10010f54(&local_b0);
    uVar7 = FUN_100169d4(param_4);
    if (uVar7 < 7) {
      FUN_1001693c(auStack_90,param_4);
      FUN_10010fd0(&local_b0);
      return uStack_24;
    }
    return 1;
  case 5:
    cVar4 = FUN_1000c850(param_4,bVar5,auStack_80);
    if (cVar4 == '\0') {
      if (param_1 == '\0') {
        local_b0 = 0x24;
      }
      else {
        local_b0 = 0xd;
      }
      puStack_ac = (undefined2 *)auStack_7c;
      FUN_10010f54(&local_b0);
      auStack_7c[0] = uStack_7d;
      FUN_10010fd0(&local_b0);
      return uStack_24;
    }
    return 1;
  case 6:
    cVar4 = FUN_1000c850(param_4,bVar5,auStack_78);
    if (cVar4 != '\0') {
      return 1;
    }
    return 1;
  case 7:
  case 8:
  case 9:
  case 10:
  case 0xb:
    if (param_1 == '\0') {
      return uStack_24;
    }
    iVar6 = *(int *)(puVar1 + (uint)bVar5 * 0x24);
    if (iVar6 == 7) {
      local_b0 = 0x10;
    }
    else if (iVar6 == 8) {
      local_b0 = 0x11;
    }
    else if (iVar6 == 9) {
      local_b0 = 0x12;
    }
    else if (iVar6 == 10) {
      local_b0 = 0x13;
    }
    else if (iVar6 == 0xb) {
      local_b0 = 0x14;
    }
    puStack_ac = auStack_74;
    FUN_10010f54(&local_b0);
    FUN_1000c850(param_4,bVar5,auStack_70);
    auStack_74[0] = uStack_6e;
    FUN_10010fd0(&local_b0);
    return uStack_24;
  case 0xc:
    FUN_1000d5b0(param_4,&uStack_5c);
    if (uStack_5c < *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18)) {
      return uStack_24;
    }
    if (*(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c) < uStack_5c) {
      return uStack_24;
    }
    local_b0 = 0x22;
    puStack_ac = (undefined2 *)auStack_58;
    FUN_10010f54(&local_b0);
    auStack_58[0] = (undefined1)uStack_5c;
    FUN_10010fd0(&local_b0);
    return uStack_24;
  case 0xd:
    FUN_1000d5b0(param_4,&uStack_6c);
    if (uStack_6c < *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18)) {
      return uStack_24;
    }
    if (*(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c) < uStack_6c) {
      return uStack_24;
    }
    local_b0 = 0x21;
    puStack_ac = (undefined2 *)auStack_68;
    FUN_10010f54(&local_b0);
    auStack_68[0] = (undefined1)uStack_6c;
    FUN_10010fd0(&local_b0);
    return uStack_24;
  case 0xe:
    FUN_1000d5b0(param_4,&uStack_64);
    if (uStack_64 < *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18)) {
      return uStack_24;
    }
    if (*(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c) < uStack_64) {
      return uStack_24;
    }
    local_b0 = 0x23;
    puStack_ac = (undefined2 *)auStack_60;
    FUN_10010f54(&local_b0);
    auStack_60[0] = (undefined1)uStack_64;
    FUN_10010fd0(&local_b0);
    return uStack_24;
  case 0xf:
    FUN_1000d5b0(param_4,&iStack_54);
    if (iStack_54 < *(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x18)) {
      return uStack_24;
    }
    if (*(int *)(puVar1 + (uint)bVar5 * 0x24 + 0x1c) < iStack_54) {
      return uStack_24;
    }
    *(int *)PTR_DAT_10006154 = iStack_54;
    return uStack_24;
  case 0x10:
    FUN_1000d5b0(param_4,&uStack_40);
    uVar3 = FUN_1000dc00(0x40);
    FUN_1001b38c(uVar3,PTR_DAT_100060dc,6);
    FUN_1001b544(uVar3,PTR_s_USTATUS_100060e0);
    FUN_1001b544(uVar3,PTR_DAT_100060e4);
    FUN_1001b544(uVar3,PTR_s_DEVICE_100060e8);
    FUN_1001b544(uVar3,PTR_DAT_100060ec);
    FUN_1001b544(uVar3,PTR_DAT_100060f0);
    FUN_1001b544(uVar3,PTR_DAT_100060f4);
    FUN_10007430(auStack_50,PTR_DAT_10006090,uStack_40);
    FUN_1001b544(uVar3,auStack_50);
    FUN_1001b544(uVar3,PTR_DAT_100060ec);
    FUN_1001b544(uVar3,PTR_DAT_100060f8);
    FUN_1000cd44(uVar3,1);
    return uStack_24;
  case 0x11:
    FUN_1000c850(param_4,bVar5,&iStack_30);
    if (iStack_30 != 1) {
      return 5;
    }
    iVar6 = FUN_1000e394();
    if (!(bool)in_b10) {
      return uStack_24;
    }
    if (iVar6 < -2) {
      return uStack_24;
    }
    return 1;
  case 0x12:
    FUN_1000c850(param_4,bVar5,&iStack_2c);
    if (iStack_2c != 0) {
      return uStack_24;
    }
    FUN_1001375c(1);
    return uStack_24;
  case 0x13:
    uStack_28 = 0xffffffff;
    FUN_1000c850(param_4,bVar5,&uStack_28);
    if (1 < uStack_28) {
      return uStack_24;
    }
    FUN_1001375c(2,&uStack_28);
    return uStack_24;
  default:
    return uStack_24;
  }
  FUN_10010fd0(&local_b0);
  return uStack_24;
}


