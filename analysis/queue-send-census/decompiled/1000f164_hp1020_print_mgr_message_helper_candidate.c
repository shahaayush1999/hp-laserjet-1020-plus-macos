/* Function: 1000f164 hp1020_print_mgr_message_helper_candidate */


/* low confidence: Print-manager helper from message-producer pass */

void hp1020_print_mgr_message_helper_candidate(int param_1)

{
  undefined4 local_50 [2];
  undefined4 uStack_48;
  undefined4 uStack_44;
  undefined4 uStack_40;
  undefined4 *puStack_3c;
  undefined4 auStack_30 [12];

  uStack_40 = 0x1b;
  puStack_3c = auStack_30;
  hp1020_datastore_read_locked_candidate(&uStack_40);
  auStack_30[0] = *(undefined4 *)(param_1 + 0x5c);
  hp1020_datastore_write_notify_unlock_candidate(&uStack_40);
  uStack_40 = 0x1c;
  puStack_3c = auStack_30;
  hp1020_datastore_read_locked_candidate(&uStack_40);
  auStack_30[0] = *(undefined4 *)(param_1 + 0x58);
  hp1020_datastore_write_notify_unlock_candidate(&uStack_40);
  local_50[0] = 0x2e;
  uStack_48 = *(undefined4 *)(param_1 + 0x58);
  uStack_44 = *(undefined4 *)(param_1 + 0x48);
  hp1020_queue_send_candidate(10,local_50);
  *(undefined1 *)(param_1 + 0x6b) = 1;
  return;
}
