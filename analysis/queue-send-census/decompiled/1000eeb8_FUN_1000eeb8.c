/* Function: 1000eeb8 FUN_1000eeb8 */


void FUN_1000eeb8(int param_1)

{
  undefined *puVar1;
  int iVar2;
  undefined4 local_50;
  int *piStack_4c;
  undefined4 auStack_40 [3];
  int *piStack_34;
  int aiStack_30 [12];

  if (*(int *)(param_1 + 0x70) == 0) {
    local_50 = 0x1c;
    piStack_4c = aiStack_30;
    hp1020_datastore_read_locked_candidate(&local_50);
    hp1020_datastore_write_notify_unlock_candidate(&local_50);
    piStack_34 = (int *)hp1020_runtime_service_candidate(0x10,1);
    auStack_40[0] = 0x2f;
    *(undefined2 *)(piStack_34 + 3) = *(undefined2 *)(param_1 + 0x6c);
    iVar2 = *(int *)(param_1 + 0x48);
    *piStack_34 = iVar2;
    piStack_34[2] = (uint)*(byte *)(param_1 + 0x6a);
    if (iVar2 == 0) {
      piStack_34[1] = 0;
    }
    else {
      piStack_34[1] = aiStack_30[0];
    }
    hp1020_queue_send_candidate(10,auStack_40);
    local_50 = 0x1b;
    piStack_4c = aiStack_30;
    hp1020_datastore_read_locked_candidate(&local_50);
    aiStack_30[0] = 0;
    hp1020_datastore_write_notify_unlock_candidate(&local_50);
    local_50 = 0x1c;
    piStack_4c = aiStack_30;
    hp1020_datastore_read_locked_candidate(&local_50);
    aiStack_30[0] = 0;
    hp1020_datastore_write_notify_unlock_candidate(&local_50);
    puVar1 = PTR_DAT_100062e4;
    hp1020_runtime_service_2_candidate(*(undefined4 *)(*(int *)PTR_DAT_100062e4 + 0xc));
    FUN_10013050(puVar1);
    hp1020_runtime_service_2_candidate();
    iVar2 = *(int *)puVar1;
    if (iVar2 != 0) {
      hp1020_print_mgr_message_helper_candidate(*(undefined4 *)(iVar2 + 0xc));
    }
  }
  return;
}
