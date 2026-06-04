/* Function: 10016164 FUN_10016164 */


undefined4 FUN_10016164(undefined4 *param_1)

{
  int *piVar1;
  undefined *puVar2;
  undefined4 uVar3;
  uint uVar4;
  undefined4 local_40;
  undefined4 uStack_3c;
  int iStack_34;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  
  puVar2 = PTR_DAT_10006920;
  switch(*param_1) {
  case 0xd:
    *param_1 = 0xe;
    FUN_10013658(1,param_1);
    break;
  case 0xf:
    local_40 = 0x25;
    uStack_3c = 0;
    PTR_DAT_10006920[0x28] = 1;
    *(undefined4 *)(puVar2 + 0x68) = 0;
    *(undefined4 *)(puVar2 + 0x6c) = 0;
    FUN_10013658(1,&local_40);
    FUN_10016098();
    break;
  case 0x11:
    uVar4 = FUN_10015df8(0);
    puVar2 = PTR_DAT_10006920;
    if ((uVar4 & 0xffff & DAT_10005e34) == 0) {
      iStack_34 = *(int *)(PTR_DAT_10006920 + 0x68);
      if (iStack_34 != 0) {
        local_40 = 0x11;
        FUN_100180dc(PTR_DAT_1000699c,&local_40,0xffffffff);
        *(undefined4 *)(puVar2 + 0x68) = 0;
      }
      iStack_34 = *(int *)(puVar2 + 0x6c);
      if (iStack_34 != 0) {
        local_40 = 0xb;
        FUN_10013620(0,&local_40);
        *(undefined4 *)(puVar2 + 0x6c) = 0;
      }
    }
    break;
  case 0x18:
    FUN_10015df8(1);
    break;
  case 0x19:
    uStack_2c = 2;
    uStack_30 = 0x16;
    FUN_10013658(1,&uStack_30);
    break;
  case 0x1a:
    FUN_10015dd0(1);
    FUN_100160a8();
    FUN_10015df8(0);
    break;
  case 0x40:
    PTR_DAT_10006920[0x28] = 0;
    *(undefined4 *)(puVar2 + 0x38) = 1;
  case 0xb:
    FUN_10015df8(0);
    puVar2 = PTR_DAT_10006920;
    piVar1 = (int *)(PTR_DAT_10006920 + 0x68);
    PTR_DAT_10006920[0x28] = 0;
    if (*piVar1 == 0) {
      *(undefined4 *)(puVar2 + 0x68) = param_1[3];
    }
    else if (*(int *)(puVar2 + 0x6c) == 0) {
      *(undefined4 *)(puVar2 + 0x6c) = param_1[3];
      return 0;
    }
    puVar2 = PTR_DAT_10006920;
    uVar3 = FUN_100162b0(*(undefined2 *)(*(int *)(PTR_DAT_10006920 + 0x68) + 0x80));
    *(undefined4 *)(puVar2 + 0x48) = uVar3;
    FUN_10015d14();
    if (**(int **)(puVar2 + 0x68) == 7) {
      *(undefined4 *)(puVar2 + 0x38) = 1;
    }
    if (*(int *)(puVar2 + 0x38) == 0) {
      FUN_10015c68(DAT_100069a4);
    }
    else {
      uVar4 = FUN_10015c68(DAT_100069a0);
      if ((uVar4 & DAT_10005e6c) == 0) {
        *(undefined4 *)(puVar2 + 0x38) = 1;
        return 0;
      }
    }
  }
  return 0;
}


