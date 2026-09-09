/* Function: 10016164 hp1020_engine_message_dispatch_candidate */


undefined4 hp1020_engine_message_dispatch_candidate(undefined4 *param_1)

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
    hp1020_queue_send_candidate(1,param_1);
    break;
  case 0xf:
    local_40 = 0x25;
    uStack_3c = 0;
    PTR_DAT_10006920[0x28] = 1;
    *(undefined4 *)(puVar2 + 0x68) = 0;
    *(undefined4 *)(puVar2 + 0x6c) = 0;
    hp1020_queue_send_candidate(1,&local_40);
    FUN_10016098();
    break;
  case 0x11:
    uVar4 = hp1020_engine_status_poll_candidate(0);
    puVar2 = PTR_DAT_10006920;
    if ((uVar4 & 0xffff & DAT_10005e34) == 0) {
      iStack_34 = *(int *)(PTR_DAT_10006920 + 0x68);
      if (iStack_34 != 0) {
        local_40 = 0x11;
        threadx_queue_send_wait_candidate(PTR_DAT_1000699c,&local_40,0xffffffff);
        *(undefined4 *)(puVar2 + 0x68) = 0;
      }
      iStack_34 = *(int *)(puVar2 + 0x6c);
      if (iStack_34 != 0) {
        local_40 = 0xb;
        hp1020_send_or_raise_engine_msg_candidate(0,&local_40);
        *(undefined4 *)(puVar2 + 0x6c) = 0;
      }
    }
    break;
  case 0x18:
    hp1020_engine_status_poll_candidate(1);
    break;
  case 0x19:
    uStack_2c = 2;
    uStack_30 = 0x16;
    hp1020_queue_send_candidate(1,&uStack_30);
    break;
  case 0x1a:
    FUN_10015dd0(1);
    hp1020_engine_preflight_candidate();
    hp1020_engine_status_poll_candidate(0);
    break;
  case 0x40:
    PTR_DAT_10006920[0x28] = 0;
    *(undefined4 *)(puVar2 + 0x38) = 1;
  case 0xb:
    hp1020_engine_status_poll_candidate(0);
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
    uVar3 = hp1020_engine_lookup_media_record_candidate
                      (*(undefined2 *)(*(int *)(PTR_DAT_10006920 + 0x68) + 0x80));
    *(undefined4 *)(puVar2 + 0x48) = uVar3;
    FUN_10015d14();
    if (**(int **)(puVar2 + 0x68) == 7) {
      *(undefined4 *)(puVar2 + 0x38) = 1;
    }
    if (*(int *)(puVar2 + 0x38) == 0) {
      hp1020_engine_status_io_candidate(DAT_100069a4);
    }
    else {
      uVar4 = hp1020_engine_status_io_candidate(DAT_100069a0);
      if ((uVar4 & DAT_10005e6c) == 0) {
        *(undefined4 *)(puVar2 + 0x38) = 1;
        return 0;
      }
    }
  }
  return 0;
}
